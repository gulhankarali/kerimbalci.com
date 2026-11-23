"""datasets modulunun ve dataset/ altindaki gercek veri setinin testleri.

Ag veya API gerektirmez; her `uv run pytest` calismasinda kosar.
"""

import json

import pytest

from kerimbalci_com.datasets import DatasetError, load_factuality, validate_record

VALID = {"id": "x-1", "input": "Soru?", "expected_output": "Cevap.", "category": "direct_fact"}


def test_gercek_factuality_dataseti_gecerli():
    """Depodaki dataset/factuality dosyalari semaya uyar ve bos degildir."""
    records = load_factuality()
    assert records
    assert {r["category"] for r in records} == {
        "direct_fact", "false_premise", "unanswerable", "time_sensitive"
    }


@pytest.mark.parametrize(
    "patch, message",
    [
        ({"input": ""}, "'input'"),
        ({"category": "baska"}, "gecersiz kategori"),
        ({"category": "false_premise"}, "false_claim"),
        ({"category": "time_sensitive"}, "valid_as_of"),
        ({"category": "time_sensitive", "valid_as_of": "23.11.2026"}, "ISO"),
    ],
)
def test_validate_record_hatalari_yakalar(patch, message):
    with pytest.raises(DatasetError, match=message):
        validate_record({**VALID, **patch})


def test_load_factuality_tekrarlanan_idyi_yakalar(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps([VALID]), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps([VALID]), encoding="utf-8")
    with pytest.raises(DatasetError, match="Tekrarlanan id"):
        load_factuality(tmp_path)


def test_load_factuality_bos_klasor(tmp_path):
    with pytest.raises(DatasetError, match="JSON dosyasi yok"):
        load_factuality(tmp_path)
