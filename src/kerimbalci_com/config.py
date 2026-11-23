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


def _env_float(key: str) -> float | None:
    """Ortam degiskenini float'a cevirir; tanimsiz veya bossa None."""
    value = os.getenv(key, "").strip()
    return float(value) if value else None


def _env_list(key: str) -> tuple[str, ...]:
    """Virgulle ayrilmis ortam degiskenini temizlenmis demete cevirir; bossa ()."""
    return tuple(item.strip() for item in os.getenv(key, "").split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Ortamdan okunan uygulama ayarlari."""

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "kerimbalci-com"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", default=False))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    judge_model: str | None = field(default_factory=lambda: os.getenv("JUDGE_MODEL"))
    hf_chatbot_url: str | None = field(default_factory=lambda: os.getenv("HF_CHATBOT_URL"))
    hf_token: str | None = field(default_factory=lambda: os.getenv("HF_TOKEN"))
    chatbot_endpoint: str = field(default_factory=lambda: os.getenv("CHATBOT_API_ENDPOINT", "/cevapla"))
    factuality_judge_level: int = field(
        default_factory=lambda: int(os.getenv("FACTUALITY_JUDGE_LEVEL", "3"))
    )
    # Bos birakilirsa hakem YAML'indaki threshold kullanilir.
    factuality_threshold: float | None = field(
        default_factory=lambda: _env_float("EVAL_FACTUALITY_THRESHOLD")
    )

    eval_concurrency: int = field(default_factory=lambda: int(os.getenv("EVAL_CONCURRENCY", "4")))
    eval_tags: tuple[str, ...] = field(default_factory=lambda: _env_list("EVAL_TAGS"))
    eval_report_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / os.getenv("EVAL_REPORT_DIR", "reports")
    )

    http_timeout: int = field(default_factory=lambda: int(os.getenv("HTTP_TIMEOUT", "30")))
    site_url: str = field(default_factory=lambda: os.getenv("SITE_URL", "https://kerimbalci.com"))
    site_workdir: Path = field(
        default_factory=lambda: PROJECT_ROOT / os.getenv("SITE_WORKDIR", ".cache/site")
    )
    crawl_user_agent: str = field(
        default_factory=lambda: os.getenv("CRAWL_USER_AGENT", "Mozilla/5.0 (compatible; kerimbalci-com-eval)")
    )

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
