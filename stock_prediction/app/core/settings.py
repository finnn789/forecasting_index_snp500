"""
app/core/settings.py — Runtime settings via pydantic-settings.

Nilai diambil dari environment variables atau file .env.
Gunakan `from app.core.settings import settings` di seluruh aplikasi.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    stock_api_key: str | None = None
    news_api_key: str | None = None

    lstm_model_path: str = "data/artifacts/lstm_weights/"
    finbert_model_name: str = "ProsusAI/finbert"
    finbert_local_path: str = "models/finbert/models--ProsusAI--finbert"

    data_filter_start: str = "2018-01-02"
    data_filter_end: str = "2024-03-04"


settings = Settings()
