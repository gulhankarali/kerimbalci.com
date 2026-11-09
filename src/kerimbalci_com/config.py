"""Uygulama ayarlari.

Tum ayarlar ortam degiskenlerinden (.env dosyasi veya sistem ortami) okunur.
Kodun icine sabit deger (hardcoding) yazilmaz; yeni bir ayar gerektiginde
once .env.example dosyasina eklenir, sonra buradan okunur.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Proje kok dizini: bu dosyanin konumundan dinamik olarak bulunur.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# .env dosyasini yukle (dosya yoksa sessizce gecer, sistem ortami kullanilir).
load_dotenv(PROJECT_ROOT / ".env")


def _env_bool(key: str, default: bool = False) -> bool:
    """Ortam degiskenini bool'a cevirir: '1', 'true', 'yes', 'on' -> True."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Ortamdan okunan uygulama ayarlari."""

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "kerimbalci-com"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", default=False))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def get_settings() -> Settings:
    """Guncel ortam degiskenlerinden yeni bir Settings nesnesi olusturur."""
    return Settings()


def setup_logging(settings: Settings | None = None) -> logging.Logger:
    """Ayarlardaki seviyeye gore logging'i yapilandirir.

    DEBUG=true ise seviye otomatik olarak DEBUG'a cekilir.
    """
    settings = settings or get_settings()
    level = logging.DEBUG if settings.debug else getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    return logging.getLogger(settings.app_name)
