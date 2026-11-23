# Factuality Dataset

Chatbot'un kerimbalci.com hakkında **doğru bilgi** verip vermediğini ölçen
soru-cevap setleri (100 kayıt). Kaynak: sitenin **tamamı** — sitemap'teki
52 yazı, 9 sayfa ve 10 seri/etiket sayfası (2026-11-23 itibarıyla). Sorular
68 farklı sayfaya dağıtılmıştır; tek sayfadan en fazla 3 soru vardır.

Her kaydın `evidence` alanı kaynak sayfadan **birebir alıntıdır** ve
oluşturma sırasında sayfa metninde geçtiği otomatik doğrulanmıştır.
Ücretli yazılarda yalnızca paywall öncesi public kısım kullanılmıştır.

| Dosya | Ne ölçer? |
|---|---|
| `direct_facts.json` | Tek doğru cevabı olan olgu soruları (biyografi, üyelik). |
| `false_premise.json` | İçinde yanlış bilgi olan sorular; chatbot öncülü **düzeltmeli**, onaylamamalı. |
| `unanswerable.json` | Sitede cevabı olmayan sorular; chatbot **uydurmamalı**, bilmediğini söylemeli. |
| `time_sensitive.json` | Değişebilecek bilgiler; `valid_as_of` tarihinden sonra yeniden doğrulanmalı. |

## Kayıt şeması

```json
{
  "id": "fact-001",                 // zorunlu, tüm dosyalarda benzersiz
  "input": "Soru",                  // zorunlu
  "expected_output": "Beklenen",    // zorunlu
  "category": "direct_fact",        // zorunlu: direct_fact | false_premise | unanswerable | time_sensitive
  "source_url": "https://...",      // kaynak sayfa (genel unanswerable'da null olabilir)
  "evidence": "...",                // kaynak sayfadan birebir alıntı (kanıt)
  "false_claim": "...",             // false_premise için zorunlu
  "valid_as_of": "2026-11-23",      // time_sensitive için zorunlu
  "notes": "..."                    // opsiyonel
}
```

`input` / `expected_output` alanları deepeval `Golden` ile birebir uyumludur.
Yapı `tests/unit/test_datasets.py` ile doğrulanır (`uv run pytest tests/unit/test_datasets.py`).

## Chatbot'u bu setle değerlendirme

```bash
uv run deepeval test run tests/factuality/           # hepsi (ücretli: hakem modele 100 istek)
uv run pytest -m eval tests/factuality/ -k unanswerable   # tek kategori
```

Her kategori kendi hakem kriteriyle puanlanır (bkz. `judges/factuality_judge/`).
Hakem: `judges/factuality_judge/` (seviye `.env` → `FACTUALITY_JUDGE_LEVEL`).
Eşik: YAML'daki `threshold`; `.env` → `EVAL_FACTUALITY_THRESHOLD` doluysa o.

## Bakım

`time_sensitive` kayıtları (son yazı, üyelik içerikleri, basım planları)
site güncellendikçe eskir; `valid_as_of` tarihine bakarak periyodik olarak
yeniden doğrulayın.
