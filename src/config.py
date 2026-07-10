"""App settings (pydantic-settings, reads from .env / environment) and shared logger."""
from __future__ import annotations

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Azil Insurance Analytics"
    azil_api_base_url: str = "https://demo.azilinsurance.co.ke/backend/api"
    azil_api_email: str = ""
    azil_api_password: str = ""
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_logger(name: str) -> logging.Logger:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return logging.getLogger(name)
