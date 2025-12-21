from __future__ import annotations

import hashlib
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mintcode_api.audit import add_audit_log
from mintcode_api.db import SessionLocal
from mintcode_api.dev_security import require_dev, rate_limit_voucher
from mintcode_api.models import DeveloperIdempotencyKey, RedeemTask, RedeemTaskProviderState, Voucher
from mintcode_api.schemas import DevRedeemCreateRequest, DevRedeemTaskResponse


router = APIRouter(prefix="/dev", tags=["dev"])


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_public_task_id() -> str:
    return "t_" + secrets.token_urlsafe(16)


def _to_dev_response(task: RedeemTask, st: Optional[RedeemTaskProviderState]) -> DevRedeemTaskResponse:
    expires_at = None
    if st is not None and getattr(st, "expires_at", None) is not None:
        expires_at = st.expires_at.replace(tzinfo=None).isoformat() + "Z"

    code = None
    final = None
    voucher_consumed = None

    if task.status in ("CODE_READY", "DONE"):
        code = task.result_code
        final = True
        voucher_consumed = True
    elif task.status in ("FAILED", "CANCELED"):
        final = True
        voucher_consumed = False

    return DevRedeemTaskResponse(
        task_id=str(task.public_id or ""),
        status=task.status,
        phone=getattr(st, "phone", None),
        expires_at=expires_at,
        code=code,
        final=final,
        voucher_consumed=voucher_consumed,
    )


def _get_task_by_public_id(db: Session, public_id: str) -> RedeemTask:
    task = db.execute(select(RedeemTask).where(RedeemTask.public_id == public_id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TASK_NOT_FOUND")
    return task


@router.post("/redeem", response_model=DevRedeemTaskResponse, dependencies=[Depends(require_dev)])
def dev_redeem_create(
    request: Request,
    payload: DevRedeemCreateRequest,
    db: Session = Depends(_get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> DevRedeemTaskResponse:
    voucher_code = payload.voucher.strip()

    rate_limit_voucher(db, voucher_code)

    voucher = db.execute(select(Voucher).where(Voucher.code == voucher_code).limit(1)).scalar_one_or_none()
    if voucher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VOUCHER_INVALID")

    dev_key_id = str(getattr(request.state, "dev_key_id", ""))
    body_sha = str(getattr(request.state, "body_sha256", ""))
    ip = getattr(getattr(request, "client", None), "host", None)
    voucher_hash = hashlib.sha256(voucher_code.encode("utf-8")).hexdigest()

    idem_sha = None
    if idempotency_key:
        idem_sha = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()

    if idempotency_key and idem_sha:
        existing_idem = db.execute(
            select(DeveloperIdempotencyKey)
            .where(
                DeveloperIdempotencyKey.dev_key_id == dev_key_id,
                DeveloperIdempotencyKey.idempotency_key_sha256 == idem_sha,
            )
            .limit(1)
        ).scalar_one_or_none()
        if existing_idem is not None:
            if str(existing_idem.request_sha256) != body_sha:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="IDEMPOTENCY_KEY_CONFLICT")
            task = db.execute(select(RedeemTask).where(RedeemTask.id == existing_idem.task_id).limit(1)).scalar_one()
            st = db.execute(
                select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)
            ).scalar_one_or_none()
            add_audit_log(
                db,
                actor_type="DevKey",
                actor_id=dev_key_id,
                ip=ip,
                action="dev.redeem.create",
                target_type="RedeemTask",
                target_id=str(task.public_id or ""),
                detail={"voucher_sha256": voucher_hash, "idempotency_key": idempotency_key or ""},
            )
            db.commit()
            return _to_dev_response(task, st)

    task = db.execute(select(RedeemTask).where(RedeemTask.voucher_id == voucher.id).limit(1)).scalar_one_or_none()
    if task is None:
        task = RedeemTask(
            public_id=_generate_public_task_id(),
            voucher_id=voucher.id,
            sku_id=voucher.sku_id,
            status="PENDING",
            result_code=None,
        )
        db.add(task)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            task = db.execute(select(RedeemTask).where(RedeemTask.voucher_id == voucher.id).limit(1)).scalar_one()
    else:
        if task.status in ("CODE_READY", "DONE"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VOUCHER_CONSUMED")
        if task.status in ("CANCELED", "FAILED"):
            st = db.execute(
                select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)
            ).scalar_one_or_none()
            if st is not None:
                db.delete(st)
                db.flush()
            db.add(RedeemTaskProviderState(task_id=task.id, provider="fivesim"))
            task.status = "PENDING"
            task.result_code = None
            db.commit()

    if not task.public_id:
        task.public_id = _generate_public_task_id()
        db.commit()

    if idempotency_key:
        db.add(
            DeveloperIdempotencyKey(
                dev_key_id=dev_key_id,
                idempotency_key_sha256=str(idem_sha or ""),
                idempotency_key_raw=idempotency_key,
                request_sha256=body_sha,
                task_id=task.id,
            )
        )
        db.commit()

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    add_audit_log(
        db,
        actor_type="DevKey",
        actor_id=dev_key_id,
        ip=ip,
        action="dev.redeem.create",
        target_type="RedeemTask",
        target_id=str(task.public_id or ""),
        detail={"voucher_sha256": voucher_hash, "idempotency_key": idempotency_key or ""},
    )
    db.commit()
    return _to_dev_response(task, st)


@router.get("/redeem/{task_id}", response_model=DevRedeemTaskResponse, dependencies=[Depends(require_dev)])
def dev_redeem_get(task_id: str, db: Session = Depends(_get_db)) -> DevRedeemTaskResponse:
    task = _get_task_by_public_id(db, task_id)
    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    return _to_dev_response(task, st)


@router.get("/redeem/{task_id}/wait", response_model=DevRedeemTaskResponse, dependencies=[Depends(require_dev)])
def dev_redeem_wait(task_id: str, timeout: int = 30, db: Session = Depends(_get_db)) -> DevRedeemTaskResponse:
    timeout = int(timeout or 0)
    if timeout < 1:
        timeout = 1
    if timeout > 30:
        timeout = 30

    end = time.time() + timeout

    while True:
        task = _get_task_by_public_id(db, task_id)
        st = db.execute(
            select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)
        ).scalar_one_or_none()

        if task.status == "CODE_READY":
            r = _to_dev_response(task, st)
            r.final = True
            r.voucher_consumed = True
            return r

        if task.status in ("DONE", "FAILED", "CANCELED"):
            return _to_dev_response(task, st)

        now = time.time()
        if now >= end:
            resp = _to_dev_response(task, st)
            resp.retry_after_seconds = 2
            return resp

        time.sleep(1)


@router.post("/redeem/{task_id}/cancel", response_model=DevRedeemTaskResponse, dependencies=[Depends(require_dev)])
def dev_redeem_cancel(task_id: str, request: Request, db: Session = Depends(_get_db)) -> DevRedeemTaskResponse:
    task = _get_task_by_public_id(db, task_id)

    if task.status in ("CODE_READY", "DONE"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TASK_ALREADY_CODE_READY")

    if task.status == "CANCELED":
        st = db.execute(
            select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)
        ).scalar_one_or_none()
        return _to_dev_response(task, st)

    task.status = "CANCELED"
    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    if st is not None:
        st.last_error = "user_canceled"
    dev_key_id = str(getattr(request.state, "dev_key_id", ""))
    ip = getattr(getattr(request, "client", None), "host", None)
    add_audit_log(
        db,
        actor_type="DevKey",
        actor_id=dev_key_id,
        ip=ip,
        action="dev.redeem.cancel",
        target_type="RedeemTask",
        target_id=str(task.public_id or ""),
        detail=None,
    )
    db.commit()
    return _to_dev_response(task, st)
