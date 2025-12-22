from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AdminGenerateVouchersRequest(BaseModel):
    sku_id: Optional[str] = Field(default=None, max_length=64)
    count: int = Field(ge=1, le=100000)

    length: int = Field(default=32, ge=12, le=64)

    label: Optional[str] = Field(default=None, max_length=32)
    label_length: int = Field(default=6, ge=2, le=16)
    label_pos: int = Field(default=8, ge=0, le=64)


class RedeemCreateRequest(BaseModel):
    code: str = Field(min_length=6, max_length=128)


class RedeemTaskResponse(BaseModel):
    task_id: int
    sku_id: str
    status: str
    result_code: Optional[str] = None
    phone: Optional[str] = None
    order_id: Optional[int] = None
    upstream_status: Optional[str] = None
    price: Optional[float] = None
    country: Optional[str] = None
    provider_started_at: Optional[str] = None
    expires_at: Optional[str] = None


class RedeemTaskActionRequest(BaseModel):
    code: str = Field(min_length=6, max_length=128)


class DevRedeemCreateRequest(BaseModel):
    voucher: str = Field(min_length=6, max_length=128)


class DevRedeemTaskResponse(BaseModel):
    task_id: str
    status: str
    phone: Optional[str] = None
    expires_at: Optional[str] = None
    code: Optional[str] = None
    final: Optional[bool] = None
    voucher_consumed: Optional[bool] = None
    retry_after_seconds: Optional[int] = None


class AdminCreateDevKeyResponse(BaseModel):
    dev_key_id: str
    dev_key_secret: str
    enabled: bool
    name: Optional[str] = None
    created_at: str


class AdminCreateDevKeyRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)


class AdminDevKeyItem(BaseModel):
    dev_key_id: str
    enabled: bool
    name: Optional[str] = None
    created_at: str
    updated_at: str


class AdminSkuProviderConfigUpsertRequest(BaseModel):
    provider: str = Field(default="fivesim", max_length=32)
    category: str = Field(default="activation", max_length=16)
    country: str = Field(max_length=64)
    operator: str = Field(default="any", max_length=64)
    product: str = Field(max_length=64)
    reuse: bool = Field(default=False)
    voice: bool = Field(default=False)
    poll_interval_seconds: int = Field(default=5, ge=1, le=300)


class AdminSkuProviderConfigResponse(BaseModel):
    sku_id: str
    provider: str
    category: str
    country: str
    operator: str
    product: str
    reuse: bool
    voice: bool
    poll_interval_seconds: int


class AdminSkuProviderConfigHistoryItem(BaseModel):
    id: int
    sku_id: str
    provider: str
    category: str
    country: str
    operator: str
    product: str
    reuse: bool
    voice: bool
    poll_interval_seconds: int
    created_at: str


class AdminSkuProviderConfigSuccessItem(BaseModel):
    id: int
    sku_id: str
    fingerprint: str
    provider: str
    category: str
    country: str
    operator: str
    product: str
    reuse: bool
    voice: bool
    poll_interval_seconds: int
    success_count: int
    total_success_cost: float
    avg_success_cost: float
    first_success_at: str
    last_success_at: str
