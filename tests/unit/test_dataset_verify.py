"""dataset_builder.verify: evidence alintilarinin site metninde dogrulanmasi.

Gercek site metni (.cache/site) git'te olmadigi icin gercek dataset kontrolu,
metin yoksa atlanir (skip).
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


def test_verify_bosluk_ve_nbsp_normalize_edilir(tmp_path):
    records = [{"id": "a", "source_url": "https://site/sayfa/", "evidence": "İlk satır. İkinci cümle."}]
    assert verify_evidence(records, _workdir(tmp_path)) == []


def test_verify_sorunlari_raporlar(tmp_path):
    records = [
        {"id": "a", "source_url": "https://site/sayfa/", "evidence": "Sitede olmayan cümle."},
        {"id": "b", "source_url": "https://site/yok/", "evidence": "x"},
        {"id": "c", "source_url": None, "evidence": None},  # kaynaksiz: atlanir
    ]
    problems = verify_evidence(records, _workdir(tmp_path))
    assert len(problems) == 2
    assert problems[0].startswith("a:") and "bulunamadi" in problems[0]
    assert problems[1].startswith("b:") and "manifest" in problems[1]


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_gercek_dataset_kanitlari_site_metninde(name):
    workdir = get_settings().site_workdir
    if not (workdir / "manifest.json").exists():
        pytest.skip("Site metni yok (uv run python -m kerimbalci_com.dataset_builder crawl)")
    assert verify_evidence(load_records(SCHEMAS[name]), workdir) == []
