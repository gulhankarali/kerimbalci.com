"""dataset_builder.verify: verifying evidence quotes against the site text.

The real site text (.cache/site) is not in git, so the real dataset check is
skipped when the text is missing.
"""

import json

import pytest

from kerimbalci_com.config import get_settings
from kerimbalci_com.dataset_builder.verify import verify_evidence
from kerimbalci_com.datasets import SCHEMAS, load_records


def _workdir(tmp_path):
    (tmp_path / "text").mkdir()
    (tmp_path / "text" / "sayfa.txt").write_text('{"meta": 1}\nİlk satır.  İkinci cümle.', encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps({"sayfa": "https://site/sayfa/"}), encoding="utf-8")
    return tmp_path


def test_verify_normalizes_whitespace_and_nbsp(tmp_path):
    records = [{"id": "a", "source_url": "https://site/sayfa/", "evidence": "İlk satır. İkinci cümle."}]
    assert verify_evidence(records, _workdir(tmp_path)) == []


def test_verify_reports_problems(tmp_path):
    records = [
        {"id": "a", "source_url": "https://site/sayfa/", "evidence": "A sentence that is not on the site."},
        {"id": "b", "source_url": "https://site/missing/", "evidence": "x"},
        {"id": "c", "source_url": None, "evidence": None},  # no source: skipped
    ]
    problems = verify_evidence(records, _workdir(tmp_path))
    assert len(problems) == 2
    assert problems[0].startswith("a:") and "not found" in problems[0]
    assert problems[1].startswith("b:") and "manifest" in problems[1]


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_real_dataset_evidence_is_in_site_text(name):
    workdir = get_settings().site_workdir
    if not (workdir / "manifest.json").exists():
        pytest.skip("No site text (uv run python -m kerimbalci_com.dataset_builder crawl)")
    assert verify_evidence(load_records(SCHEMAS[name]), workdir) == []
