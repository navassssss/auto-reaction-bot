import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

class Settings(BaseSettings):
    telegram_bot_token: str
    telegram_webhook_secret: str
    admin_telegram_ids: str  # Comma-separated list of IDs
    database_url: str
    worker_count: int = 2
    log_level: str = "INFO"
    port: int = 8000
    host: str = "0.0.0.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.admin_telegram_ids:
            return []
        try:
            return [int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()]
        except ValueError:
            return []

settings = Settings()

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
