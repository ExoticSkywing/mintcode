from __future__ import annotations

import datetime as dt
import time
from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import Base, SessionLocal, engine
from mintcode_api.models import RedeemTask, RedeemTaskProviderState, SkuProviderConfig


def _process_one(task: RedeemTask, db: Session) -> None:
    from fivesim import ActivationProduct, Country, FiveSim, HostingProduct, Operator, Order, OrderAction, Status

    now = dt.datetime.utcnow()

    cfg = db.execute(select(SkuProviderConfig).where(SkuProviderConfig.sku_id == task.sku_id).limit(1)).scalar_one_or_none()
    if cfg is None:
        st = db.execute(
            select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)
        ).scalar_one_or_none()
        if st is None:
            st = RedeemTaskProviderState(task_id=task.id, provider="fivesim", last_error="missing_sku_provider_config")
            db.add(st)
        else:
            st.last_error = "missing_sku_provider_config"
        task.status = "FAILED"
        return

    if not settings.fivesim_api_key:
        st = db.execute(
            select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)
        ).scalar_one_or_none()
        if st is None:
            st = RedeemTaskProviderState(task_id=task.id, provider="fivesim", last_error="missing_fivesim_api_key")
            db.add(st)
        else:
            st.last_error = "missing_fivesim_api_key"
        task.status = "FAILED"
        return

    st = db.execute(select(RedeemTaskProviderState).where(RedeemTaskProviderState.task_id == task.id).limit(1)).scalar_one_or_none()
    if st is None:
        st = RedeemTaskProviderState(task_id=task.id, provider=cfg.provider)
        db.add(st)
        db.flush()

    fs = FiveSim(api_key=settings.fivesim_api_key)

    try:
        if st.order_id is None:
            country = Country(cfg.country)
            operator = Operator(cfg.operator)
            if cfg.category == "hosting":
                product = HostingProduct(cfg.product)
            else:
                product = ActivationProduct(cfg.product)

            order = fs.user.buy_number(
                country=country,
                operator=operator,
                product=product,
                reuse=bool(cfg.reuse),
                voice=bool(cfg.voice),
            )
            st.order_id = int(order.id)
            st.phone = order.phone
            st.upstream_status = str(order.status)
            st.next_poll_at = now + dt.timedelta(seconds=int(cfg.poll_interval_seconds))
            task.status = "PENDING"
            return

        order = Order.from_order_id(int(st.order_id))
        checked = fs.user.order(OrderAction.CHECK, order)
        st.upstream_status = str(checked.status)

        sms_list = checked.sms or []
        code = None
        for sms in reversed(sms_list):
            if getattr(sms, "activation_code", None):
                code = sms.activation_code
                break

        if code:
            task.result_code = code
            task.status = "DONE"
            try:
                fs.user.order(OrderAction.FINISH, checked)
            except Exception:
                pass
            return

        if checked.status in (Status.CANCELED, Status.TIMEOUT, Status.BANNED):
            task.status = "FAILED"
            st.last_error = "upstream_status=" + str(checked.status)
            return

        st.next_poll_at = now + dt.timedelta(seconds=int(cfg.poll_interval_seconds))
        task.status = "PENDING"
    except Exception as e:
        st.last_error = str(e)
        st.next_poll_at = now + dt.timedelta(seconds=max(5, int(getattr(cfg, "poll_interval_seconds", 5))))
        task.status = "PENDING"


def _claim_next(db: Session) -> Optional[RedeemTask]:
    now = dt.datetime.utcnow()
    for _ in range(5):
        task_id = db.execute(
            select(RedeemTask.id)
            .outerjoin(RedeemTaskProviderState, RedeemTaskProviderState.task_id == RedeemTask.id)
            .where(RedeemTask.status == "PENDING")
            .where(or_(RedeemTaskProviderState.next_poll_at.is_(None), RedeemTaskProviderState.next_poll_at <= now))
            .order_by(RedeemTask.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if task_id is None:
            return None

        res = db.execute(
            update(RedeemTask)
            .where(RedeemTask.id == task_id)
            .where(RedeemTask.status == "PENDING")
            .values(status="PROCESSING")
        )
        if getattr(res, "rowcount", 0) == 1:
            db.flush()
            return db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    return None


def run_loop(poll_seconds: float = 1.0) -> None:
    Base.metadata.create_all(bind=engine)
    while True:
        db = SessionLocal()
        try:
            task = _claim_next(db)
            if task is None:
                db.commit()
                time.sleep(poll_seconds)
                continue

            try:
                _process_one(task, db)
                db.commit()
            except Exception:
                db.rollback()
                db2 = SessionLocal()
                try:
                    t2 = db2.execute(select(RedeemTask).where(RedeemTask.id == task.id).limit(1)).scalar_one_or_none()
                    if t2 is not None and t2.status in ("PENDING", "PROCESSING"):
                        t2.status = "FAILED"
                        db2.commit()
                finally:
                    db2.close()
        finally:
            db.close()


if __name__ == "__main__":
    _ = settings.database_url
    run_loop()
