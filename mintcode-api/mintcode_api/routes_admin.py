from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import SessionLocal
from mintcode_api.models import RedeemTask, Voucher, VoucherBatch
from mintcode_api.schemas import AdminGenerateVouchersRequest
from mintcode_api.security import require_admin
from mintcode_api.vouchers import generate_voucher_codes


router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/vouchers/generate", response_class=PlainTextResponse)
def admin_generate_vouchers(payload: AdminGenerateVouchersRequest, db: Session = Depends(_get_db)) -> str:
    sku_id = payload.sku_id or payload.label or "default"

    batch = VoucherBatch(sku_id=sku_id, count=payload.count)
    db.add(batch)
    db.flush()

    inserted = 0
    label_pos = min(payload.label_pos, payload.length)

    while inserted < payload.count:
        need = payload.count - inserted
        candidates = generate_voucher_codes(
            count=need,
            length=payload.length,
            label=payload.label,
            secret=settings.voucher_secret if payload.label else None,
            label_length=payload.label_length,
            label_pos=label_pos,
        )

        values = [
            {
                "batch_id": batch.id,
                "sku_id": sku_id,
                "code": c,
            }
            for c in candidates
        ]

        # MySQL: INSERT IGNORE 会忽略 uq_vouchers_code 冲突
        stmt = insert(Voucher).prefix_with("IGNORE")
        db.execute(stmt, values)
        db.flush()

        # 不依赖 rowcount（不同驱动/执行模式下可能不存在），直接回查当前批次已插入数量
        inserted = int(
            db.execute(select(func.count()).select_from(Voucher).where(Voucher.batch_id == batch.id)).scalar_one()
        )

    db.commit()

    # 回查该 batch 的最终 code，确保返回精确数量且都是落库成功的
    final_codes = db.execute(
        select(Voucher.code).where(Voucher.batch_id == batch.id).order_by(Voucher.id.asc())
    ).scalars().all()

    return "\n".join(final_codes)


@router.get("/batches")
def admin_list_batches(
    sku_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(_get_db),
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))

    q = select(VoucherBatch).order_by(VoucherBatch.id.desc()).limit(limit)
    if sku_id:
        q = q.where(VoucherBatch.sku_id == sku_id)

    batches = db.execute(q).scalars().all()
    out: List[Dict[str, Any]] = []
    for b in batches:
        created_at: dt.datetime = b.created_at
        out.append(
            {
                "id": b.id,
                "sku_id": b.sku_id,
                "count": b.count,
                "created_at": created_at.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )
    return out


@router.get("/vouchers/export/batch/{batch_id}", response_class=PlainTextResponse)
def admin_export_vouchers_by_batch(batch_id: int, db: Session = Depends(_get_db)) -> str:
    codes = db.execute(
        select(Voucher.code).where(Voucher.batch_id == batch_id).order_by(Voucher.id.asc())
    ).scalars().all()
    return "\n".join(codes)


@router.get("/vouchers/export/latest", response_class=PlainTextResponse)
def admin_export_vouchers_latest_by_sku(sku_id: str, db: Session = Depends(_get_db)) -> str:
    batch_id = db.execute(
        select(VoucherBatch.id).where(VoucherBatch.sku_id == sku_id).order_by(VoucherBatch.id.desc()).limit(1)
    ).scalar_one_or_none()
    if batch_id is None:
        return ""

    codes = db.execute(
        select(Voucher.code).where(Voucher.batch_id == int(batch_id)).order_by(Voucher.id.asc())
    ).scalars().all()
    return "\n".join(codes)


@router.get("/redeem/tasks")
def admin_list_redeem_tasks(
    status: Optional[str] = None,
    sku_id: Optional[str] = None,
    limit: int = 50,
    before_id: Optional[int] = None,
    db: Session = Depends(_get_db),
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))

    q = (
        select(RedeemTask, Voucher.code)
        .join(Voucher, Voucher.id == RedeemTask.voucher_id)
        .order_by(RedeemTask.id.desc())
        .limit(limit)
    )
    if status:
        q = q.where(RedeemTask.status == status)
    if sku_id:
        q = q.where(RedeemTask.sku_id == sku_id)
    if before_id is not None:
        q = q.where(RedeemTask.id < int(before_id))

    rows = db.execute(q).all()
    out: List[Dict[str, Any]] = []
    for task, voucher_code in rows:
        created_at: dt.datetime = task.created_at
        updated_at: dt.datetime = task.updated_at
        out.append(
            {
                "id": task.id,
                "sku_id": task.sku_id,
                "status": task.status,
                "result_code": task.result_code,
                "voucher_id": task.voucher_id,
                "voucher_code": voucher_code,
                "created_at": created_at.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                "updated_at": updated_at.replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )
    return out
