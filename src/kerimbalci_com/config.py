"""Application settings.

All settings are read from environment variables (.env file or the system
environment). Nothing is hardcoded; a new setting is first added to
.env.example and then read here.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Project root, derived dynamically from the location of this file.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load the .env file (silently skipped if missing; the system environment is used).
load_dotenv(PROJECT_ROOT / ".env")


def _env_bool(key: str, default: bool = False) -> bool:
    """Converts an environment variable to bool: '1', 'true', 'yes', 'on' -> True."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(key: str) -> float | None:
    """Converts an environment variable to float; None if unset or empty."""
    value = os.getenv(key, "").strip()
    return float(value) if value else None


def _env_list(key: str) -> tuple[str, ...]:
    """Converts a comma-separated environment variable to a cleaned tuple; () if empty."""
    return tuple(item.strip() for item in os.getenv(key, "").split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    """Application settings read from the environment."""

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "kerimbalci-com"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _env_bool("DEBUG", default=False))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    judge_model: str | None = field(default_factory=lambda: os.getenv("JUDGE_MODEL"))
    hf_chatbot_url: str | None = field(default_factory=lambda: os.getenv("HF_CHATBOT_URL"))
    hf_token: str | None = field(default_factory=lambda: os.getenv("HF_TOKEN"))
    chatbot_endpoint: str = field(default_factory=lambda: os.getenv("CHATBOT_API_ENDPOINT", "/cevapla"))
    chatbot_timeout: float = field(default_factory=lambda: float(os.getenv("CHATBOT_TIMEOUT", "60")))
    chatbot_max_retries: int = field(default_factory=lambda: int(os.getenv("CHATBOT_MAX_RETRIES", "2")))
    chatbot_retry_backoff: float = field(
        default_factory=lambda: float(os.getenv("CHATBOT_RETRY_BACKOFF", "2"))
    )
    eval_min_pass_rate: float = field(
        default_factory=lambda: float(os.getenv("EVAL_MIN_PASS_RATE", "0.85"))
    )
    eval_compare_min_delta: float = field(
        default_factory=lambda: float(os.getenv("EVAL_COMPARE_MIN_DELTA", "0.2"))
    )
    eval_expected_behavior: bool = field(
        default_factory=lambda: _env_bool("EVAL_EXPECTED_BEHAVIOR", default=True)
    )
    factuality_judge_level: int = field(
        default_factory=lambda: int(os.getenv("FACTUALITY_JUDGE_LEVEL", "3"))
    )
    # If empty, the threshold from the judge YAML is used.
    factuality_threshold: float | None = field(
        default_factory=lambda: _env_float("EVAL_FACTUALITY_THRESHOLD")
    )
    hallucination_judge_level: int = field(
        default_factory=lambda: int(os.getenv("HALLUCINATION_JUDGE_LEVEL", "3"))
    )
    # If empty, the threshold from the judge YAML is used.
    hallucination_threshold: float | None = field(
        default_factory=lambda: _env_float("EVAL_HALLUCINATION_THRESHOLD")
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
    """Builds a new Settings object from the current environment variables."""
    return Settings()


def setup_logging(settings: Settings | None = None) -> logging.Logger:
    """Configures logging according to the configured level.

    With DEBUG=true the level is automatically set to DEBUG.
    """
    settings = settings or get_settings()
    level = logging.DEBUG if settings.debug else getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    return logging.getLogger(settings.app_name)
