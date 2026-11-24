# Hallucination Dataset

Chatbot'un kerimbalci.com'da **olmayan bir şeyi uydurup uydurmadığını** ölçen
50 golden kayıt. Factuality "cevap doğru mu?" diye sorar; hallucination
"cevaba sitede dayanağı olmayan bir şey eklendi mi?" diye sorar. Sorular,
chatbot'u bilinen bir uydurma tuzağına çekecek şekilde tasarlanmıştır.

Her kaydın `evidence` alanı kaynak sayfadan **birebir alıntıdır** ve
otomatik olarak doğrulanır (`dataset_builder verify hallucination`).
Factuality setindeki `false_premise` / `unanswerable` sorularıyla
çakışmamaya dikkat edilmiştir.

| Dosya | Kategori | Kayıt | Ne ölçer? |
|---|---|---|---|
| `fabricated_detail.json` | `fabricated_detail` | 14 | Konu sitede var, sorulan ayrıntı yok (kitap adı, kanal, miktar, tez başlığı…). Chatbot "sitede yok" demeli, sitede olanı vermeli. |
| `fake_attribution.json` | `fake_attribution` | 12 | Söz/fikir yanlış kişiye atfediliyor (Pericles, Tanpınar, Avi, anne…) ya da hiç söylenmemiş. Chatbot doğru kişiyi söylemeli veya sözün sitede olmadığını belirtmeli. |
| `entity_confusion.json` | `entity_confusion` | 12 | Sitede birbirine benzeyen iki varlık (Durham/Burch, Adalet Divanı/Ceza Mahkemesi, Avi/Yael…). Özellikler doğru varlığa verilmeli. |
| `unsupported_addition.json` | `unsupported_addition` | 12 | Cevap sitede var; risk, genel bilgiden kaynaksız ekleme (tarih, isim, tanım). Chatbot sitede yazanla sınırlı kalmalı. |

## Kayıt şeması

```json
{
  "id": "fab-001",                  // zorunlu, benzersiz (fab | attr | conf | add)
  "input": "Soru",                  // zorunlu
  "expected_output": "Beklenen",    // zorunlu; yalnızca site içeriğine dayanır
  "category": "fabricated_detail",  // zorunlu: yukarıdaki 4 kategoriden biri
  "hallucination_trap": "...",      // zorunlu: chatbot'un uydurmaya meyilli olacağı şey
  "source_url": "https://...",      // zorunlu: kaynak sayfa
  "evidence": "..."                 // zorunlu: kaynak sayfadan birebir alıntı (→ LLMTestCase.context)
}
```

`hallucination_trap` Level 3 hakemine `{hallucination_trap}` yer tutucusuyla
verilir; hakem cevabın bu tuzağa düşüp düşmediğini ayrıca kontrol eder.
Şema `src/kerimbalci_com/datasets.py` → `HALLUCINATION` ile tanımlıdır ve
`tests/unit/test_datasets.py` ile doğrulanır.

## Çalıştırma

```bash
HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fab-001    # tek kayıt
uv run pytest -m eval tests/hallucination/ -k fake_attribution                      # tek kategori
uv run deepeval test run tests/hallucination/                                       # hepsi (ücretli)
uv run python -m kerimbalci_com.evals hallucination --limit 3                       # paralel runner
```

Hakem: `judges/hallucination_judge/` (seviye `.env` → `HALLUCINATION_JUDGE_LEVEL`).
Eşik: YAML'daki `threshold`; `.env` → `EVAL_HALLUCINATION_THRESHOLD` doluysa o.

## Bakım

Kayıt eklerken veya değiştirirken önce alıntıyı doğrulayın:

```bash
uv run python -m kerimbalci_com.dataset_builder verify hallucination
```

`fabricated_detail` ve `fake_attribution` kayıtları "sitede yok" iddiasına
dayanır; site güncellendikçe bu bilgilerin hâlâ sitede olmadığını kontrol edin.
