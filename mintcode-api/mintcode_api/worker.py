from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import socket
import time
from types import SimpleNamespace
from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from mintcode_api.config import settings
from mintcode_api.db import Base, SessionLocal, engine
from mintcode_api.models import RedeemTask, RedeemTaskProviderState, SkuProviderConfig, SkuProviderConfigSuccess


_WORKER_OWNER = os.environ.get("WORKER_ID") or f"{socket.gethostname()}:{os.getpid()}"


def _process_one(task: RedeemTask, db: Session) -> None:
    from fivesim import ActivationProduct, Category, Country, FiveSim, HostingProduct, Operator, Order, OrderAction, Status
    from fivesim.json_response import _parse_order

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

    def _collect_success_config(cost: float) -> None:
        fp_src = "|".join(
            [
                str(task.sku_id),
                str(cfg.provider),
                str(cfg.category),
                str(cfg.country),
                str(cfg.operator),
                str(cfg.product),
                "1" if bool(cfg.reuse) else "0",
                "1" if bool(cfg.voice) else "0",
                str(int(cfg.poll_interval_seconds)),
            ]
        )
        fp = hashlib.sha1(fp_src.encode("utf-8")).hexdigest()
        row = db.execute(
            select(SkuProviderConfigSuccess)
            .where(SkuProviderConfigSuccess.sku_id == task.sku_id)
            .where(SkuProviderConfigSuccess.fingerprint == fp)
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            row = SkuProviderConfigSuccess(
                sku_id=task.sku_id,
                fingerprint=fp,
                provider=cfg.provider,
                category=cfg.category,
                country=cfg.country,
                operator=cfg.operator,
                product=cfg.product,
                reuse=bool(cfg.reuse),
                voice=bool(cfg.voice),
                poll_interval_seconds=int(cfg.poll_interval_seconds),
                success_count=1,
                total_success_cost=float(cost or 0),
                first_success_at=now,
                last_success_at=now,
            )
            db.add(row)
        else:
            row.success_count = int(row.success_count) + 1
            row.last_success_at = now
            try:
                row.total_success_cost = float(row.total_success_cost or 0) + float(cost or 0)
            except Exception:
                row.total_success_cost = float(cost or 0)

    try:
        def _release_with_status(new_status: str) -> None:
            task.status = new_status
            if hasattr(task, "processing_owner"):
                task.processing_owner = None
            if hasattr(task, "processing_until"):
                task.processing_until = None

        def _release_only() -> None:
            if hasattr(task, "processing_owner"):
                task.processing_owner = None
            if hasattr(task, "processing_until"):
                task.processing_until = None

        if task.status == "CANCELED":
            _release_only()
            return

        if task.status == "DONE":
            _release_only()
            return

        if task.result_code and st.order_id is not None and st.expires_at is not None and now >= st.expires_at:
            try:
                fs.user.order(OrderAction.FINISH, Order.from_order_id(int(st.order_id)))
            except Exception:
                pass
            _release_with_status("DONE")
            return

        if task.status == "CODE_READY":
            if st.order_id is None:
                _release_only()
                return
            if st.expires_at is not None and now >= st.expires_at:
                try:
                    fs.user.order(OrderAction.FINISH, Order.from_order_id(int(st.order_id)))
                except Exception:
                    pass
                _release_with_status("DONE")
            else:
                _release_only()
            return

        if st.order_id is not None and task.status in ("PENDING", "PROCESSING", "WAITING_SMS"):
            try:
                deadline = st.expires_at
                if deadline is None:
                    started_at = getattr(st, "created_at", None)
                    if started_at is not None:
                        deadline = started_at + dt.timedelta(seconds=float(settings.redeem_wait_seconds))
                if deadline is not None and now >= deadline:
                    try:
                        fs.user.order(OrderAction.CANCEL, Order.from_order_id(int(st.order_id)))
                    except Exception:
                        pass
                    _release_with_status("FAILED")
                    st.last_error = "expired"
                    return
            except Exception:
                pass

        if st.order_id is None:
            buy_attempts = int(getattr(st, "buy_attempts", 0) or 0)
            max_buy_attempts = int(getattr(settings, "max_buy_attempts", 3) or 3)
            if buy_attempts >= max_buy_attempts:
                st.last_error = f"max_buy_attempts_exceeded={buy_attempts}"
                _release_with_status("FAILED")
                return

            inflight_until = getattr(st, "buy_inflight_until", None)
            if inflight_until is not None and now < inflight_until:
                st.next_poll_at = now + dt.timedelta(seconds=1)
                _release_with_status("WAITING_SMS")
                return

            st.buy_attempts = buy_attempts + 1
            st.last_buy_attempt_at = now
            st.buy_inflight_until = now + dt.timedelta(seconds=int(getattr(settings, "buy_inflight_seconds", 20) or 20))
            db.flush()
            db.commit()

            country = Country(cfg.country)
            op = (cfg.operator or "").strip().lower()
            try:
                operator = Operator(op)
            except Exception:
                if op == "any":
                    operator = Operator.ANY_OPERATOR
                elif not re.fullmatch(r"[a-z0-9]+", op):
                    st.last_error = "invalid_operator=" + str(cfg.operator)
                    _release_with_status("FAILED")
                    return
                else:
                    operator = SimpleNamespace(value=op)
            product_key = (cfg.product or "").strip().lower()
            if not product_key:
                st.last_error = "invalid_product=" + str(cfg.product)
                _release_with_status("FAILED")
                return

            if not re.fullmatch(r"[a-z0-9_-]+", product_key):
                st.last_error = "invalid_product=" + str(cfg.product)
                _release_with_status("FAILED")
                return

            # SDK enums may lag behind 5sim official product list. If enum conversion fails,
            # bypass SDK buy_number() (which enforces isinstance checks) and call the API path directly.
            if cfg.category == "hosting":
                try:
                    product = HostingProduct(product_key)
                    order = fs.user.buy_number(
                        country=country,
                        operator=operator,
                        product=product,
                        reuse=False,
                        voice=False,
                    )
                except Exception:
                    api_result = fs.user._GET(
                        use_token=True,
                        path=["buy", Category.HOSTING.value, country.value, operator.value, product_key],
                        parameters={},
                    )
                    order = fs.user._parse_json(input=api_result, into_object=_parse_order)
            else:
                try:
                    product = ActivationProduct(product_key)
                    order = fs.user.buy_number(
                        country=country,
                        operator=operator,
                        product=product,
                        reuse=bool(cfg.reuse),
                        voice=bool(cfg.voice),
                    )
                except Exception:
                    params = {}
                    if bool(cfg.reuse):
                        params["reuse"] = "1"
                    if bool(cfg.voice):
                        params["voice"] = "1"
                    api_result = fs.user._GET(
                        use_token=True,
                        path=["buy", Category.ACTIVATION.value, country.value, operator.value, product_key],
                        parameters=params,
                    )
                    order = fs.user._parse_json(input=api_result, into_object=_parse_order)

            st.order_id = int(order.id)
            st.phone = order.phone
            st.upstream_status = str(order.status)
            st.price = float(getattr(order, "price", 0) or 0)
            st.expires_at = getattr(order, "expires_at", None)
            st.next_poll_at = now + dt.timedelta(seconds=int(cfg.poll_interval_seconds))
            st.buy_inflight_until = None
            st.last_error = None
            _release_with_status("WAITING_SMS")
            db.flush()
            db.commit()
            return

        order = Order.from_order_id(int(st.order_id))
        checked = fs.user.order(OrderAction.CHECK, order)
        st.upstream_status = str(checked.status)
        if getattr(checked, "price", None) is not None:
            st.price = float(getattr(checked, "price", 0) or 0)
        st.last_error = None

        sms_list = checked.sms or []
        if not sms_list:
            try:
                sms_list = fs.user.get_sms_inbox_list(checked) or []
            except Exception:
                sms_list = []
        code = None
        for sms in reversed(sms_list):
            if getattr(sms, "activation_code", None):
                code = sms.activation_code
                break

        if code:
            already_had_code = bool(task.result_code)
            task.result_code = code
            task.status = "CODE_READY"
            _release_only()
            if not already_had_code:
                _collect_success_config(float(getattr(checked, "price", 0) or 0))
            return

        if checked.status in (Status.CANCELED, Status.TIMEOUT, Status.BANNED):
            _release_with_status("FAILED")
            st.last_error = "upstream_status=" + str(checked.status)
            return

        st.next_poll_at = now + dt.timedelta(seconds=int(cfg.poll_interval_seconds))
        _release_with_status("WAITING_SMS")
    except Exception as e:
        st.last_error = str(e)
        st.next_poll_at = now + dt.timedelta(seconds=max(5, int(getattr(cfg, "poll_interval_seconds", 5))))
        _release_with_status("WAITING_SMS")


def _claim_next(db: Session) -> Optional[RedeemTask]:
    now = dt.datetime.utcnow()
    lease_until = now + dt.timedelta(seconds=int(getattr(settings, "worker_lease_seconds", 30)))
    for _ in range(5):
        task_id = db.execute(
            select(RedeemTask.id)
            .outerjoin(RedeemTaskProviderState, RedeemTaskProviderState.task_id == RedeemTask.id)
            .where(
                or_(
                    RedeemTask.status.in_(["PENDING", "WAITING_SMS"]),
                    (RedeemTask.status == "PROCESSING")
                    & (RedeemTask.processing_until.is_not(None))
                    & (RedeemTask.processing_until <= now),
                    (RedeemTask.status == "CODE_READY") & (RedeemTaskProviderState.expires_at.is_not(None)) & (RedeemTaskProviderState.expires_at <= now),
                )
            )
            .where(or_(RedeemTaskProviderState.next_poll_at.is_(None), RedeemTaskProviderState.next_poll_at <= now))
            .order_by(RedeemTask.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if task_id is None:
            return None

        res = db.execute(
            update(RedeemTask)
            .where(RedeemTask.id == task_id)
            .where(
                or_(
                    RedeemTask.status.in_(["PENDING", "WAITING_SMS", "CODE_READY"]),
                    (RedeemTask.status == "PROCESSING")
                    & (RedeemTask.processing_until.is_not(None))
                    & (RedeemTask.processing_until <= now),
                )
            )
            .values(status="PROCESSING", processing_owner=_WORKER_OWNER, processing_until=lease_until)
        )
        if getattr(res, "rowcount", 0) == 1:
            db.flush()
            return db.execute(select(RedeemTask).where(RedeemTask.id == task_id).limit(1)).scalar_one_or_none()
    return None


def run_loop(poll_seconds: float = 1.0) -> None:
    if bool(getattr(settings, "db_auto_create_tables", True)):
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
                        if hasattr(t2, "processing_owner"):
                            t2.processing_owner = None
                        if hasattr(t2, "processing_until"):
                            t2.processing_until = None
                        db2.commit()
                finally:
                    db2.close()
        finally:
            db.close()


if __name__ == "__main__":
    _ = settings.database_url
    run_loop()
