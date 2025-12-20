from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mintcode_api.db import Base


class VoucherBatch(Base):
    __tablename__ = "voucher_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())

    vouchers: Mapped[list[Voucher]] = relationship("Voucher", back_populates="batch")


class Voucher(Base):
    __tablename__ = "vouchers"
    __table_args__ = (
        UniqueConstraint("code", name="uq_vouchers_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("voucher_batches.id"), nullable=False)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())

    batch: Mapped[VoucherBatch] = relationship("VoucherBatch", back_populates="vouchers")


class RedeemTask(Base):
    __tablename__ = "redeem_tasks"
    __table_args__ = (
        UniqueConstraint("voucher_id", name="uq_redeem_tasks_voucher_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column(Integer, ForeignKey("vouchers.id"), nullable=False)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    processing_owner: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processing_until: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: dt.datetime.utcnow(), onupdate=lambda: dt.datetime.utcnow()
    )


class SkuProviderConfigHistory(Base):
    __tablename__ = "sku_provider_config_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="fivesim")
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="activation")
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(64), nullable=False, default="any")
    product: Mapped[str] = mapped_column(String(64), nullable=False)
    reuse: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())


class SkuProviderConfigSuccess(Base):
    __tablename__ = "sku_provider_config_successes"
    __table_args__ = (
        UniqueConstraint("sku_id", "fingerprint", name="uq_sku_provider_config_successes_sku_fp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(40), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="fivesim")
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="activation")
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(64), nullable=False, default="any")
    product: Mapped[str] = mapped_column(String(64), nullable=False)
    reuse: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_success_cost: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    first_success_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())
    last_success_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: dt.datetime.utcnow(), onupdate=lambda: dt.datetime.utcnow()
    )


class SkuProviderConfig(Base):
    __tablename__ = "sku_provider_configs"

    sku_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="fivesim")
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="activation")
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(64), nullable=False, default="any")
    product: Mapped[str] = mapped_column(String(64), nullable=False)
    reuse: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: dt.datetime.utcnow(), onupdate=lambda: dt.datetime.utcnow()
    )


class RedeemTaskProviderState(Base):
    __tablename__ = "redeem_task_provider_states"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("redeem_tasks.id"), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="fivesim")
    order_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    upstream_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    expires_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    next_poll_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    buy_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_buy_attempt_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    buy_inflight_until: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=lambda: dt.datetime.utcnow())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: dt.datetime.utcnow(), onupdate=lambda: dt.datetime.utcnow()
    )

    task: Mapped[RedeemTask] = relationship("RedeemTask")
