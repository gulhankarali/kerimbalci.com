"""Tests for the datasets module and the real datasets under dataset/.

No network or API needed; runs on every `uv run pytest`.
"""

import json

import pytest

from kerimbalci_com.datasets import (
    HALLUCINATION, DatasetError, load_factuality, load_hallucination, validate_record,
)

VALID = {"id": "x-1", "input": "Question?", "expected_output": "Answer.", "category": "direct_fact"}


def test_real_factuality_dataset_is_valid():
    """The dataset/factuality files in the repo match the schema and are not empty."""
    records = load_factuality()
    assert records
    assert {r["category"] for r in records} == {
        "direct_fact", "false_premise", "unanswerable", "time_sensitive"
    }


def test_real_hallucination_dataset_is_valid():
    """50 records, 4 categories; every record has evidence and a trap description."""
    records = load_hallucination()
    assert len(records) == 50
    assert {r["category"] for r in records} == set(HALLUCINATION.categories)
    assert all(r["source_url"].startswith("https://") for r in records)


H_VALID = {**VALID, "category": "fabricated_detail", "source_url": "https://x/",
           "evidence": "quote", "hallucination_trap": "invention"}


@pytest.mark.parametrize("patch, message", [
    ({"evidence": ""}, "'evidence'"),
    ({"hallucination_trap": None}, "'hallucination_trap'"),
    ({"source_url": None}, "'source_url'"),
    ({"category": "direct_fact"}, "invalid category"),
])
def test_hallucination_schema(patch, message):
    validate_record(H_VALID, HALLUCINATION)
    with pytest.raises(DatasetError, match=message):
        validate_record({**H_VALID, **patch}, HALLUCINATION)


@pytest.mark.parametrize(
    "patch, message",
    [
        ({"input": ""}, "'input'"),
        ({"category": "other"}, "invalid category"),
        ({"category": "false_premise"}, "false_claim"),
        ({"category": "time_sensitive"}, "valid_as_of"),
        ({"category": "time_sensitive", "valid_as_of": "23.11.2026"}, "ISO"),
    ],
)
def test_validate_record_catches_errors(patch, message):
    with pytest.raises(DatasetError, match=message):
        validate_record({**VALID, **patch})


def test_load_factuality_catches_duplicate_id(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps([VALID]), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps([VALID]), encoding="utf-8")
    with pytest.raises(DatasetError, match="Duplicate id"):
        load_factuality(tmp_path)


def test_load_factuality_empty_folder(tmp_path):
    with pytest.raises(DatasetError, match="No JSON files"):
        load_factuality(tmp_path)
