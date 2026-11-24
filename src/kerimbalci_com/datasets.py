"""Eval veri setlerini (dataset/ klasoru) yukleyip dogrulayan yardimcilar.

Her suite'in veri seti bir `DatasetSchema` ile tanimlanir (klasor, kategoriler,
zorunlu alanlar). Yollar proje kokune gore dinamik hesaplanir (config.PROJECT_ROOT).
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from kerimbalci_com.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

DATASET_ROOT = PROJECT_ROOT / "dataset"
REQUIRED_FIELDS = ("id", "input", "expected_output", "category")


class DatasetError(ValueError):
    """Veri setindeki bir kayit semaya uymuyor."""


@dataclass(frozen=True)
class DatasetSchema:
    """Bir suite'in veri seti semasi."""

    name: str
    categories: frozenset[str]
    required: tuple[str, ...] = REQUIRED_FIELDS
    category_fields: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def directory(self) -> Path:
        return DATASET_ROOT / self.name


FACTUALITY = DatasetSchema(
    name="factuality",
    categories=frozenset({"direct_fact", "false_premise", "unanswerable", "time_sensitive"}),
    category_fields={"false_premise": ("false_claim",), "time_sensitive": ("valid_as_of",)},
)

# Hallucination kayitlarinin hepsi siteye dayanir: kanit (evidence + source_url) ve
# chatbot'un uydurmaya meyilli olacagi seyin tarifi (hallucination_trap) zorunludur.
HALLUCINATION = DatasetSchema(
    name="hallucination",
    categories=frozenset(
        {"fabricated_detail", "fake_attribution", "entity_confusion", "unsupported_addition"}
    ),
    required=(*REQUIRED_FIELDS, "source_url", "evidence", "hallucination_trap"),
)

SCHEMAS = {schema.name: schema for schema in (FACTUALITY, HALLUCINATION)}

# Geriye donuk uyumluluk (factuality icin eski adlar)
FACTUALITY_DIR = FACTUALITY.directory
CATEGORIES = FACTUALITY.categories
CATEGORY_FIELDS = FACTUALITY.category_fields
HALLUCINATION_DIR = HALLUCINATION.directory
HALLUCINATION_CATEGORIES = HALLUCINATION.categories
ALL_CATEGORIES = frozenset().union(*(s.categories for s in SCHEMAS.values()))


def validate_record(record: dict, schema: DatasetSchema = FACTUALITY) -> None:
    """Tek bir kaydi semaya gore dogrular; hata varsa DatasetError firlatir."""
    rid = record.get("id", "<id yok>")
    for key in schema.required:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DatasetError(f"{rid}: '{key}' alani eksik veya bos")
    if record["category"] not in schema.categories:
        raise DatasetError(f"{rid}: gecersiz kategori '{record['category']}'")
    for key in schema.category_fields.get(record["category"], ()):
        if not record.get(key):
            raise DatasetError(f"{rid}: '{record['category']}' icin '{key}' zorunlu")
    if record.get("valid_as_of"):
        try:
            date.fromisoformat(record["valid_as_of"])
        except ValueError as exc:
            raise DatasetError(f"{rid}: valid_as_of ISO tarih olmali") from exc


def load_records(schema: DatasetSchema, directory: Path | None = None) -> list[dict]:
    """Klasordeki tum *.json dosyalarini okur, semaya gore dogrular, tek liste dondurur."""
    directory = directory or schema.directory
    files = sorted(directory.glob("*.json"))
    if not files:
        raise DatasetError(f"{directory} altinda JSON dosyasi yok")

    records: list[dict] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            raise DatasetError(f"{path.name}: bos olmayan bir JSON listesi olmali")
        for record in data:
            validate_record(record, schema)
        records.extend(data)
        logger.debug("%s: %d kayit yuklendi", path.name, len(data))

    ids = [r["id"] for r in records]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise DatasetError(f"Tekrarlanan id: {', '.join(duplicates)}")
    return records


def load_factuality(directory: Path | None = None) -> list[dict]:
    """dataset/factuality kayitlari."""
    return load_records(FACTUALITY, directory)


def load_hallucination(directory: Path | None = None) -> list[dict]:
    """dataset/hallucination kayitlari."""
    return load_records(HALLUCINATION, directory)
