from __future__ import annotations

import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import SessionLocal
from mintcode_api.models import RedeemTask, Voucher
from mintcode_api.schemas import RedeemCreateRequest, RedeemTaskResponse


router = APIRouter()


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_mock_code() -> str:
    return str(secrets.randbelow(1_000_000)).zfill(6)


def _process_task(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
        if task is None:
            return
        if task.status not in ("PENDING", "PROCESSING"):
            return

        task.status = "PROCESSING"
        db.flush()

        task.result_code = task.result_code or _generate_mock_code()
        task.status = "DONE"
        db.commit()
    finally:
        db.close()


@router.post("/redeem", response_model=RedeemTaskResponse)
def redeem_create(
    payload: RedeemCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(_get_db),
) -> RedeemTaskResponse:
    code = payload.code.strip()

    voucher = db.execute(select(Voucher).where(Voucher.code == code).limit(1)).scalar_one_or_none()
    if voucher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid_code")

    existing = db.execute(select(RedeemTask).where(RedeemTask.voucher_id == voucher.id).limit(1)).scalar_one_or_none()
    if existing is not None:
        if settings.redeem_process_mode == "inline" and existing.status in ("PENDING", "PROCESSING"):
            background_tasks.add_task(_process_task, existing.id)
        return RedeemTaskResponse(
            task_id=existing.id,
            sku_id=existing.sku_id,
            status=existing.status,
            result_code=existing.result_code,
        )

    task = RedeemTask(
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
        # 并发情况下可能已经插入成功，回查并返回
        existing = db.execute(select(RedeemTask).where(RedeemTask.voucher_id == voucher.id).limit(1)).scalar_one()
        if settings.redeem_process_mode == "inline" and existing.status in ("PENDING", "PROCESSING"):
            background_tasks.add_task(_process_task, existing.id)
        return RedeemTaskResponse(
            task_id=existing.id,
            sku_id=existing.sku_id,
            status=existing.status,
            result_code=existing.result_code,
        )

    db.refresh(task)
    if settings.redeem_process_mode == "inline":
        background_tasks.add_task(_process_task, task.id)
    return RedeemTaskResponse(task_id=task.id, sku_id=task.sku_id, status=task.status, result_code=task.result_code)


@router.get("/redeem/{task_id}", response_model=RedeemTaskResponse)
def redeem_get(task_id: int, db: Session = Depends(_get_db)) -> RedeemTaskResponse:
    task = db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    return RedeemTaskResponse(task_id=task.id, sku_id=task.sku_id, status=task.status, result_code=task.result_code)
