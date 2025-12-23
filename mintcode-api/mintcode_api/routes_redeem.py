from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import SessionLocal
from mintcode_api.models import RedeemTask, RedeemTaskProviderState, SkuProviderConfig, Voucher
from mintcode_api.schemas import RedeemCreateRequest, RedeemTaskActionRequest, RedeemTaskResponse


router = APIRouter()


def _get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_mock_code() -> str:
    return str(secrets.randbelow(1_000_000)).zfill(6)


def _to_response(task: RedeemTask, st: Optional[RedeemTaskProviderState], db: Session) -> RedeemTaskResponse:
    started_at = None
    if st is not None and getattr(st, "created_at", None) is not None:
        started_at = st.created_at.replace(tzinfo=None).isoformat() + "Z"
    expires_at = None
    if st is not None and getattr(st, "expires_at", None) is not None:
        expires_at = st.expires_at.replace(tzinfo=None).isoformat() + "Z"
    
    country = None
    if task.sku_id:
        cfg = db.execute(select(SkuProviderConfig).where(SkuProviderConfig.sku_id == task.sku_id).limit(1)).scalar_one_or_none()
        if cfg:
            country = cfg.country

    return RedeemTaskResponse(
        task_id=task.id,
        sku_id=task.sku_id,
        status=task.status,
        result_code=task.result_code,
        phone=getattr(st, "phone", None),
        order_id=getattr(st, "order_id", None),
        upstream_status=getattr(st, "upstream_status", None),
        price=float(getattr(st, "price", 0) or 0) if getattr(st, "price", None) is not None else None,
        country=country,
        provider_started_at=started_at,
        expires_at=expires_at,
    )


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
        if existing.status in ("CODE_READY", "DONE"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="voucher_used")

        if existing.status in ("CANCELED", "FAILED"):
            st = db.execute(
                select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == existing.id).limit(1)
            ).scalar_one_or_none()
            if st is not None:
                db.delete(st)
                db.flush()
            new_st = RedeemTaskProviderState(task_id=existing.id, provider="fivesim")
            db.add(new_st)
            existing.status = "PENDING"
            existing.result_code = None
            db.commit()
            if settings.redeem_process_mode == "inline":
                background_tasks.add_task(_process_task, existing.id)
            return _to_response(existing, new_st, db)

        if settings.redeem_process_mode == "inline" and existing.status in ("PENDING", "PROCESSING"):
            background_tasks.add_task(_process_task, existing.id)
        st = db.execute(
            select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == existing.id).limit(1)
        ).scalar_one_or_none()
        return _to_response(existing, st, db)

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
        st = db.execute(
            select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == existing.id).limit(1)
        ).scalar_one_or_none()
        return _to_response(existing, st, db)

    db.refresh(task)
    if settings.redeem_process_mode == "inline":
        background_tasks.add_task(_process_task, task.id)
    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    return _to_response(task, st, db)


@router.post("/redeem/query", response_model=RedeemTaskResponse)
def redeem_query(payload: RedeemCreateRequest, db: Session = Depends(_get_db)) -> RedeemTaskResponse:
    """Query order history by voucher code."""
    code = payload.code.strip()

    voucher = db.execute(select(Voucher).where(Voucher.code == code).limit(1)).scalar_one_or_none()
    if voucher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invalid_code")

    task = db.execute(select(RedeemTask).where(RedeemTask.voucher_id == voucher.id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no_order")

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    return _to_response(task, st, db)


@router.get("/redeem/{task_id}", response_model=RedeemTaskResponse)
def redeem_get(task_id: int, db: Session = Depends(_get_db)) -> RedeemTaskResponse:
    task = db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    return _to_response(task, st, db)


@router.post("/redeem/{task_id}/cancel", response_model=RedeemTaskResponse)
def redeem_cancel(task_id: int, payload: RedeemTaskActionRequest, db: Session = Depends(_get_db)) -> RedeemTaskResponse:
    task = db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    voucher = db.execute(select(Voucher).where(Voucher.id == task.voucher_id).limit(1)).scalar_one()
    if voucher.code != payload.code.strip():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_code")

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    if st is not None and st.order_id is not None and settings.fivesim_api_key:
        try:
            from fivesim import FiveSim, Order, OrderAction

            fs = FiveSim(api_key=settings.fivesim_api_key)
            fs.user.order(OrderAction.CANCEL, Order.from_order_id(int(st.order_id)))
        except Exception:
            pass

    task.status = "CANCELED"
    if st is not None:
        st.last_error = "user_canceled"
    db.commit()
    return _to_response(task, st, db)


@router.post("/redeem/{task_id}/next", response_model=RedeemTaskResponse)
def redeem_next(task_id: int, payload: RedeemTaskActionRequest, db: Session = Depends(_get_db)) -> RedeemTaskResponse:
    task = db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    voucher = db.execute(select(Voucher).where(Voucher.id == task.voucher_id).limit(1)).scalar_one()
    if voucher.code != payload.code.strip():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_code")

    if task.status not in ("CANCELED", "FAILED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not_cancelled")

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    # prepare for next buy: clear provider state and set back to pending
    if st is not None:
        db.delete(st)
        db.flush()
    new_st = RedeemTaskProviderState(task_id=task.id, provider="fivesim")
    db.add(new_st)
    task.status = "PENDING"
    task.result_code = None
    db.commit()
    return _to_response(task, new_st, db)


@router.post("/redeem/{task_id}/complete", response_model=RedeemTaskResponse)
def redeem_complete(task_id: int, payload: RedeemTaskActionRequest, db: Session = Depends(_get_db)) -> RedeemTaskResponse:
    task = db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    voucher = db.execute(select(Voucher).where(Voucher.id == task.voucher_id).limit(1)).scalar_one()
    if voucher.code != payload.code.strip():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_code")

    if task.status not in ("CODE_READY", "DONE"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="not_ready")

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    if st is not None and st.order_id is not None and settings.fivesim_api_key:
        try:
            from fivesim import FiveSim, Order, OrderAction

            fs = FiveSim(api_key=settings.fivesim_api_key)
            fs.user.order(OrderAction.FINISH, Order.from_order_id(int(st.order_id)))
        except Exception:
            pass

    task.status = "DONE"
    db.commit()
    return _to_response(task, st, db)
