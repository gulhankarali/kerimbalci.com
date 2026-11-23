"""Eval veri setlerini (dataset/ klasoru) yukleyip dogrulayan yardimcilar.

Veri seti yolu proje kokune gore dinamik hesaplanir (config.PROJECT_ROOT).
"""

import json
import logging
from datetime import date
from pathlib import Path

from kerimbalci_com.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

FACTUALITY_DIR = PROJECT_ROOT / "dataset" / "factuality"

CATEGORIES = frozenset({"direct_fact", "false_premise", "unanswerable", "time_sensitive"})
REQUIRED_FIELDS = ("id", "input", "expected_output", "category")
CATEGORY_FIELDS = {"false_premise": ("false_claim",), "time_sensitive": ("valid_as_of",)}


class DatasetError(ValueError):
    """Veri setindeki bir kayit semaya uymuyor."""


def validate_record(record: dict) -> None:
    """Tek bir kaydi semaya gore dogrular; hata varsa DatasetError firlatir."""
    rid = record.get("id", "<id yok>")
    for key in REQUIRED_FIELDS:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DatasetError(f"{rid}: '{key}' alani eksik veya bos")
    if record["category"] not in CATEGORIES:
        raise DatasetError(f"{rid}: gecersiz kategori '{record['category']}'")
    for key in CATEGORY_FIELDS.get(record["category"], ()):
        if not record.get(key):
            raise DatasetError(f"{rid}: '{record['category']}' icin '{key}' zorunlu")
    if record["category"] == "time_sensitive":
        try:
            date.fromisoformat(record["valid_as_of"])
        except ValueError as exc:
            raise DatasetError(f"{rid}: valid_as_of ISO tarih olmali") from exc


def load_factuality(directory: Path | None = None) -> list[dict]:
    """Klasordeki tum *.json dosyalarini okur, dogrular ve tek liste dondurur."""
    directory = directory or FACTUALITY_DIR
    files = sorted(directory.glob("*.json"))
    if not files:
        raise DatasetError(f"{directory} altinda JSON dosyasi yok")

    records: list[dict] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            raise DatasetError(f"{path.name}: bos olmayan bir JSON listesi olmali")
        for record in data:
            validate_record(record)
        records.extend(data)
        logger.debug("%s: %d kayit yuklendi", path.name, len(data))

    ids = [r["id"] for r in records]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise DatasetError(f"Tekrarlanan id: {', '.join(duplicates)}")
    return records
