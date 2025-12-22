from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import time
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import SessionLocal
from mintcode_api.models import DeveloperKey, DeveloperNonce, DeveloperRateLimit


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _body_sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _canonical_string(
    method: str,
    path: str,
    query: str,
    timestamp: str,
    nonce: str,
    body_sha256: str,
) -> str:
    return "\n".join([method.upper(), path, query or "", timestamp, nonce, body_sha256])


def _b64_hmac_sha256(secret: str, msg: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(sig).decode("ascii")


def _rate_limit_increment(db: Session, scope: str, scope_id: str, window_start_ts: int, limit: int) -> None:
    stmt = mysql_insert(DeveloperRateLimit).values(
        scope=scope,
        scope_id=scope_id,
        window_start_ts=window_start_ts,
        count=1,
        created_at=dt.datetime.utcnow(),
        updated_at=dt.datetime.utcnow(),
    )
    stmt = stmt.on_duplicate_key_update(
        count=DeveloperRateLimit.count + 1,
        updated_at=dt.datetime.utcnow(),
    )
    db.execute(stmt)
    db.flush()

    row = db.execute(
        select(DeveloperRateLimit)
        .where(
            DeveloperRateLimit.scope == scope,
            DeveloperRateLimit.scope_id == scope_id,
            DeveloperRateLimit.window_start_ts == window_start_ts,
        )
        .limit(1)
    ).scalar_one()

    if int(row.count or 0) > int(limit):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="DEV_RATE_LIMITED")


async def require_dev(
    request: Request,
    db: Session = Depends(_get_db),
    x_dev_key_id: Optional[str] = Header(default=None, alias="X-Dev-Key-Id"),
    x_dev_timestamp: Optional[str] = Header(default=None, alias="X-Dev-Timestamp"),
    x_dev_nonce: Optional[str] = Header(default=None, alias="X-Dev-Nonce"),
    x_dev_signature: Optional[str] = Header(default=None, alias="X-Dev-Signature"),
) -> str:
    if not x_dev_key_id or not x_dev_timestamp or not x_dev_nonce or not x_dev_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="DEV_AUTH_MISSING_HEADERS")

    try:
        ts = int(x_dev_timestamp)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="DEV_AUTH_TIMESTAMP_OUT_OF_RANGE")

    now = int(time.time())
    if abs(now - ts) > int(settings.dev_auth_timestamp_skew_seconds):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="DEV_AUTH_TIMESTAMP_OUT_OF_RANGE")

    key = db.execute(select(DeveloperKey).where(DeveloperKey.dev_key_id == x_dev_key_id).limit(1)).scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="DEV_AUTH_INVALID_SIGNATURE")
    if not bool(key.enabled):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="DEV_AUTH_KEY_DISABLED")

    body = await request.body()
    body_sha = _body_sha256_hex(body)

    canonical = _canonical_string(
        method=request.method,
        path=request.url.path,
        query=request.url.query or "",
        timestamp=x_dev_timestamp,
        nonce=x_dev_nonce,
        body_sha256=body_sha,
    )

    expected = _b64_hmac_sha256(str(key.dev_key_secret), canonical)
    if not hmac.compare_digest(expected, x_dev_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="DEV_AUTH_INVALID_SIGNATURE")

    nonce_sha256 = hashlib.sha256(x_dev_nonce.encode("utf-8")).hexdigest()
    db.add(DeveloperNonce(dev_key_id=x_dev_key_id, ts=ts, nonce_sha256=nonce_sha256, nonce_raw=x_dev_nonce))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="DEV_AUTH_NONCE_REPLAY")

    window_start = (now // 60) * 60
    try:
        _rate_limit_increment(
            db,
            scope="dev_key",
            scope_id=x_dev_key_id,
            window_start_ts=window_start,
            limit=int(settings.dev_rate_limit_dev_key_per_min),
        )

        ip = getattr(getattr(request, "client", None), "host", None) or ""
        if ip:
            _rate_limit_increment(
                db,
                scope="ip",
                scope_id=ip,
                window_start_ts=window_start,
                limit=int(settings.dev_rate_limit_ip_per_min),
            )

        db.commit()
    except HTTPException:
        db.commit()
        raise

    request.state.dev_key_id = x_dev_key_id
    request.state.body_bytes = body
    request.state.body_sha256 = body_sha
    return x_dev_key_id


def rate_limit_voucher(db: Session, voucher: str) -> None:
    now = int(time.time())
    window_start = (now // 60) * 60
    try:
        _rate_limit_increment(
            db,
            scope="voucher",
            scope_id=voucher,
            window_start_ts=window_start,
            limit=int(settings.dev_rate_limit_voucher_per_min),
        )
        db.commit()
    except HTTPException:
        db.commit()
        raise
