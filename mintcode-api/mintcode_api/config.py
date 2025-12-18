from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    admin_api_key: str
    voucher_secret: str
    database_url: str

    redeem_process_mode: str = "inline"


settings = Settings()
