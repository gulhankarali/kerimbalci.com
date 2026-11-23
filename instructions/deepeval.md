# deepeval ve Confident AI

## Kavramlar
- **LLMTestCase:** `input` (soru), `actual_output` (chatbot cevabı),
  `expected_output` (dataset'teki doğru cevap). Factuality testinde `name`
  = kayıt id'si, `tags` = kategori.
- **Metric:** cevabı 0-1 arası puanlar; `threshold` altı = başarısız.
  - `GEval` — doğal dille yazılmış kritere göre hakem puanı. Factuality
    suite'inde her case iki GEval ile ölçülür: **Factuality** (olgular doğru
    mu?) ve **Expected Behavior** (dil, kısalık, ton, çerçeveleme —
    `judges/expected_behavior_judge/`, `EVAL_EXPECTED_BEHAVIOR`). Case ancak
    ikisi de geçerse geçer; rapor metric bazında ayrı özet de verir.
    Factuality kriterleri `judges/factuality_judge/*.yaml`'dan gelir (seviye 1-3,
    `FACTUALITY_JUDGE_LEVEL`). `evaluation_steps` + `rules` + `rubric`
    (0-10 puan bantları) GEval'e aktarılır; level 2-3'te `evidence` `context` olur.
- **Hakem (judge):** puanlamayı yapan LLM; `AnthropicModel(model=JUDGE_MODEL)`.
- **assert_test:** metrikleri çalıştırır, eşik altındaysa testi düşürür.

## Çalıştırma

```bash
uv run deepeval test run tests/factuality/   # önerilen: özet tablo + Confident AI
uv run pytest -m eval tests/factuality/      # düz pytest
```

`deepeval test run` sonunda metrik bazlı özet tablo gösterir ve
`CONFIDENT_API_KEY` tanımlıysa sonuçları Confident AI'ya yükler.

## Kendi runner'ımız

`src/kerimbalci_com/evals/` deepeval metric'lerini doğrudan `metric.measure()`
ile, thread havuzunda (`EVAL_CONCURRENCY`) çalıştırır; bu yüzden suite
metric'leri `async_mode=False` kurulur. Sonuçlar Confident AI'ya **gitmez**;
`reports/` altına JSON yazılır. Yeni suite eklemek için
`evals/suites/<ad>.py` içinde `build_suite(settings, judge_model)` yazıp
`evals/suites/__init__.py` → `SUITES`'e ekleyin.

## Confident AI
- app.confident-ai.com → proje → Settings → Project API Key →
  `.env` içinde `CONFIDENT_API_KEY`.
- Her koşu bir "test run" olarak görünür; kayıtlar id ve kategori
  etiketiyle filtrelenebilir, koşular karşılaştırılabilir.
- `.deepeval/` klasörü deepeval'in yerel önbelleği/ayarlarıdır.

## Maliyet
- Her test case = 1 chatbot çağrısı + hakem çağrıları (GEval adım üretimi
  ve puanlama). 100 kayıtlık factuality seti yüzlerce hakem isteği eder.
- Önce `-k <kategori>` veya `-k <id>` ile küçük denemeler yapın.
- Runner raporları hakem maliyetini gösterir: özet tablonun altında
  `Hakem maliyeti: $X, case başına $Y (girdi / çıktı token)`; JSON'da
  `summary.overall.usage`, tag bazında `summary.by_tag.<tag>.usage`, case
  bazında `cases[].usage`. `compare` iki koşunun maliyet farkını da yazar.
- Fiyatlar deepeval'in model tablosundan gelir. Güncel değilse `.env`'e
  `ANTHROPIC_COST_PER_INPUT_TOKEN` / `ANTHROPIC_COST_PER_OUTPUT_TOKEN`
  (token başına USD) ekleyin; deepeval bunları kendisi okur.
- Chatbot (HF Space) maliyeti rapora dahil değildir.

## Kriter değiştirme
`judges/factuality_judge/` altındaki ilgili YAML'ı düzenleyin →
`uv run pytest tests/unit/test_judges.py` →
birkaç kayıtla deneyin → Confident AI'da önceki koşuyla karşılaştırın.
