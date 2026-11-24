"""Helpers that load and validate the eval datasets (dataset/ folder).

Each suite's dataset is described by a `DatasetSchema` (folder, categories,
required fields). Paths are computed from the project root (config.PROJECT_ROOT).
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
    """A dataset record does not match the schema."""


@dataclass(frozen=True)
class DatasetSchema:
    """Dataset schema of a suite."""

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

# Every hallucination record is grounded in the site: evidence (evidence + source_url)
# and a description of what the chatbot is tempted to invent (hallucination_trap) are required.
HALLUCINATION = DatasetSchema(
    name="hallucination",
    categories=frozenset(
        {"fabricated_detail", "fake_attribution", "entity_confusion", "unsupported_addition"}
    ),
    required=(*REQUIRED_FIELDS, "source_url", "evidence", "hallucination_trap"),
)

SCHEMAS = {schema.name: schema for schema in (FACTUALITY, HALLUCINATION)}

# Backward compatibility (old names for factuality)
FACTUALITY_DIR = FACTUALITY.directory
CATEGORIES = FACTUALITY.categories
CATEGORY_FIELDS = FACTUALITY.category_fields
HALLUCINATION_DIR = HALLUCINATION.directory
HALLUCINATION_CATEGORIES = HALLUCINATION.categories
ALL_CATEGORIES = frozenset().union(*(s.categories for s in SCHEMAS.values()))


def validate_record(record: dict, schema: DatasetSchema = FACTUALITY) -> None:
    """Validates a single record against the schema; raises DatasetError on failure."""
    rid = record.get("id", "<no id>")
    for key in schema.required:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DatasetError(f"{rid}: '{key}' field is missing or empty")
    if record["category"] not in schema.categories:
        raise DatasetError(f"{rid}: invalid category '{record['category']}'")
    for key in schema.category_fields.get(record["category"], ()):
        if not record.get(key):
            raise DatasetError(f"{rid}: '{key}' is required for '{record['category']}'")
    if record.get("valid_as_of"):
        try:
            date.fromisoformat(record["valid_as_of"])
        except ValueError as exc:
            raise DatasetError(f"{rid}: valid_as_of must be an ISO date") from exc


def load_records(schema: DatasetSchema, directory: Path | None = None) -> list[dict]:
    """Reads all *.json files in the folder, validates them and returns a single list."""
    directory = directory or schema.directory
    files = sorted(directory.glob("*.json"))
    if not files:
        raise DatasetError(f"No JSON files in {directory}")

    records: list[dict] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            raise DatasetError(f"{path.name}: must be a non-empty JSON list")
        for record in data:
            validate_record(record, schema)
        records.extend(data)
        logger.debug("%s: %d records loaded", path.name, len(data))

    ids = [r["id"] for r in records]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise DatasetError(f"Duplicate id: {', '.join(duplicates)}")
    return records


def load_factuality(directory: Path | None = None) -> list[dict]:
    """Records of dataset/factuality."""
    return load_records(FACTUALITY, directory)


def load_hallucination(directory: Path | None = None) -> list[dict]:
    """Records of dataset/hallucination."""
    return load_records(HALLUCINATION, directory)
