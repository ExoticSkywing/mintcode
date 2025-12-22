from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    admin_api_key: str
    voucher_secret: str
    database_url: str

    dev_auth_timestamp_skew_seconds: int = 300

    dev_rate_limit_voucher_per_min: int = 30
    dev_rate_limit_dev_key_per_min: int = 60
    dev_rate_limit_ip_per_min: int = 120

    db_auto_create_tables: bool = True

    worker_lease_seconds: int = 30

    buy_inflight_seconds: int = 20
    max_buy_attempts: int = 3

    redeem_process_mode: str = "inline"

    redeem_wait_seconds: int = 120

    fivesim_api_key: Optional[str] = None


settings = Settings()
