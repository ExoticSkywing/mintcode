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
