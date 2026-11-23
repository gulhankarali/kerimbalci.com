# Test

Testler pytest ile yazılır; ayarlar `pyproject.toml` →
`[tool.pytest.ini_options]` (`-v --strict-markers`, canlı log INFO).

## Test türleri

| Tür | Marker | Ağ/API | Ücret | Dosyalar |
|---|---|---|---|---|
| Birim | — | Hayır | Yok | `tests/unit/` |
| Bağlantı | `integration` | Evet | Yok | `tests/integration/` |
| Eval | `integration` + `eval` | Evet | **Var** (hakem model) | `tests/<suite>/` (ör. `tests/factuality/`) |

Ortak fixture'lar (`settings`, `chatbot`, `judge_model`) `tests/conftest.py`'dedir;
ayar eksikse testi atlar. Yeni suite için `tests/<suite>/test_<suite>.py` açın.

`--strict-markers` açık olduğu için yeni marker önce `pyproject.toml`'a
eklenmelidir.

## Çalıştırma

```bash
uv run pytest                              # hepsi (eval dahil — ücretli!)
uv run pytest -m "not integration"         # sadece birim testler (hızlı, ücretsiz)
uv run pytest -m "integration and not eval"   # bağlantı testleri
uv run deepeval test run tests/factuality/   # factuality eval (100 soru)
uv run pytest -m eval tests/factuality/ -k unanswerable   # tek kategori
uv run pytest -m eval tests/factuality/ -k "fact-001"               # tek kayıt
```

Eval testleri önce `-k` ile küçük bir alt kümede denenmelidir.

### Runner (pytest dışı, paralel)

```bash
uv run python -m kerimbalci_com.evals factuality --limit 3          # duman testi
uv run python -m kerimbalci_com.evals factuality --tags unanswerable --level 3
uv run python -m kerimbalci_com.evals factuality --ids fact-001,premise-002
```

Sonunda tag bazlı özet tablo yazar ve `reports/factuality-L<N>-<zaman>.json`
oluşturur (git'e girmez). Çıkış kodu: 0 hepsi geçti, 1 başarısız/hata, 2 eksik ayar.
pytest yolu Confident AI'ya yükler; runner yerel ve paralel çalışır.

## Kurallar
- Ortam değişkenleri `monkeypatch.setenv/delenv` ile ayarlanır.
- Gerekli değişken yoksa test `pytest.skip(...)` ile atlanır.
- Dosya gerektiren birim testlerde `tmp_path` kullanılır.
- Gerçek dataset ve hakem YAML'ları için de birim test vardır; bu dosyalar
  bozulursa hızlı testler yakalar.
