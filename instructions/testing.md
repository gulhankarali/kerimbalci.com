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
oluşturur (git'e girmez).

**Kalite kapısı:** geçen case oranı `EVAL_MIN_PASS_RATE` (vars. 0.85) veya
`--min-pass-rate` değerinin altındaysa koşu başarısızdır. Hata alan case'ler
başarısız sayılır. Sonuç özet tablonun son satırında ve JSON'da
`summary.quality_gate` altında yer alır.

Çıkış kodu: 0 kapı geçti, 1 kapı kaldı, 2 eksik ayar / filtreye uyan case yok.

### Koşuları karşılaştırma (regresyon)

```bash
uv run python -m kerimbalci_com.evals.compare                    # aynı suite'in son iki raporu
uv run python -m kerimbalci_com.evals.compare --suite factuality-L3
uv run python -m kerimbalci_com.evals.compare reports/a.json reports/b.json
```

Tag bazında geçme oranı ve ortalama puan farkını, **bozulan** (geçti → kaldı),
**düzelen** (kaldı → geçti) ve durumu aynı kalıp puanı `EVAL_COMPARE_MIN_DELTA`
(vars. 0.2) kadar değişen case'leri listeler. Farklı suite/hakem seviyesi
karşılaştırılırsa uyarır. Çıkış kodu: 0 bozulma yok, 1 bozulma var, 2 rapor yok.
Chatbot veya hakem değişikliğinden önce ve sonra aynı filtreyle koşup
karşılaştırın.

## CI (GitHub Actions)

| İş akışı | Tetikleyici | Ne yapar | Ücret |
|---|---|---|---|
| `.github/workflows/ci.yml` | Her push (main) ve PR | `uv sync --locked` + `pytest -m "not integration"` | Yok |
| `.github/workflows/eval.yml` | Elle: Actions → Eval → Run workflow | Bağlantı testleri + runner (suite, seviye, tag, limit, eşik seçilir); `reports/` artifact olarak 90 gün saklanır | **Var** |

Eval iş akışı için gereken secret/variable'lar: `configuration.md` → GitHub Actions.
İki CI koşusunu karşılaştırmak için artifact'leri indirip `compare`'e iki dosya
yolu olarak verin.
pytest yolu Confident AI'ya yükler; runner yerel ve paralel çalışır.

## Kurallar
- Ortam değişkenleri `monkeypatch.setenv/delenv` ile ayarlanır.
- Gerekli değişken yoksa test `pytest.skip(...)` ile atlanır.
- Dosya gerektiren birim testlerde `tmp_path` kullanılır.
- Gerçek dataset ve hakem YAML'ları için de birim test vardır; bu dosyalar
  bozulursa hızlı testler yakalar.
