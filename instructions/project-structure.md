# Proje Yapısı

```
kerimbalci.com/
├── CLAUDE.md                 # Temel kurallar (Claude Code her oturumda okur)
├── pyproject.toml            # Proje, bağımlılıklar, pytest ayarları
├── uv.lock                   # Sabitlenmiş bağımlılık sürümleri (commit edilir)
├── .env.example              # Ortam değişkeni şablonu (commit edilir)
├── .env                      # Gerçek değerler (COMMIT EDİLMEZ)
├── .cache/                   # Taranan site metinleri, üretilen ham JSON'lar (COMMIT EDİLMEZ)
├── reports/                  # Runner JSON raporları (COMMIT EDİLMEZ)
├── .vscode/                  # launch.json (F5 debug), settings.json
├── .github/workflows/        # ci.yml (birim testler), eval.yml (elle, ücretli eval)
├── instructions/             # Bu dokümantasyon
├── dataset/
│   ├── factuality/           # Factuality eval dataset'i (4 kategori, JSON)
│   └── hallucination/        # Hallucination eval dataset'i (4 kategori, 50 kayıt)
├── judges/
│   ├── factuality_judge/     # Hakem YAML'ları: level1_basic, level2_intermediate, level3_advanced
│   ├── hallucination_judge/  # Hallucination hakemleri (aynı 3 seviye)
│   └── expected_behavior_judge/  # Davranış hakemi (dil, kısalık, ton, çerçeveleme)
├── src/kerimbalci_com/
│   ├── __init__.py           # main(): ayarları yükler, loglamayı kurar
│   ├── __main__.py           # python -m kerimbalci_com giriş noktası
│   ├── config.py             # Settings, get_settings(), setup_logging()
│   ├── chatbot.py            # ChatbotClient — HF Space'e soru gönderir
│   ├── datasets.py           # DatasetSchema, load_factuality(), load_hallucination()
│   ├── dataset_builder/      # Siteden dataset üretimi: crawl, split, merge, verify (python -m ...)
│   └── evals/
│       ├── __main__.py       # CLI: python -m kerimbalci_com.evals <suite> [--tags/--ids/--limit/--level]
│       ├── eval_suite.py     # EvalSuite: case'ler + metric fabrikası + filtre
│       ├── suite_runner.py   # run_suite(): paralel çalıştırma, CaseResult/SuiteResult
│       ├── judge_config.py   # JudgeSet, load_judge() (YAML) + build_geval()
│       ├── reporter.py       # Tag bazlı özet tablo + JSON rapor (reports/)
│       ├── compare.py        # İki raporu karşılaştırır: bozulan/düzelen case'ler
│       └── suites/
│           ├── __init__.py   # SUITES kaydı
│           ├── common.py             # Ortak: LLMTestCase + metric fabrikası
│           ├── factuality_suite.py   # dataset/factuality + judges/factuality_judge
│           └── hallucination_suite.py # dataset/hallucination + judges/hallucination_judge
└── tests/
    ├── conftest.py           # Ortak fixture'lar: settings, chatbot, judge_model
    ├── unit/                 # Ağ/API gerektirmez
    │   ├── test_config.py    # Ayarlar
    │   ├── test_datasets.py  # Dataset şeması + gerçek dataset
    │   ├── test_judges.py    # Hakem YAML şeması
    │   ├── test_dataset_builder.py  # Tarama, metin çıkarma, merge (sahte fetch)
│   ├── test_dataset_verify.py   # evidence alıntılarının site metninde doğrulanması
    │   ├── test_chatbot.py   # Zaman aşımı / yeniden deneme (sahte Gradio)
    │   ├── test_compare.py   # Rapor karşılaştırma
    │   └── test_evals.py     # Suite, runner, reporter, CLI (sahte chatbot/hakem)
    ├── integration/
    │   └── test_connections.py  # HF Space, HF token, Anthropic, JUDGE_MODEL
    ├── factuality/
    │   └── test_factuality.py   # Eval: factuality suite'i pytest/deepeval ile
    └── hallucination/
        └── test_hallucination.py  # Eval: hallucination suite'i pytest/deepeval ile
```

## Veri akışı (eval)

```
dataset/factuality/*.json ──load_factuality()──┐
                                               ▼
                         ChatbotClient.ask(input) → actual_output
                                               ▼
judges/factuality_judge/level<N>.yaml ──load_judge()/build_geval()──► GEval (hakem: JUDGE_MODEL)
  (N = FACTUALITY_JUDGE_LEVEL; evidence → context)
                                               ▼
      ┌──────────────────────────┴──────────────────────────┐
      ▼                                                     ▼
 pytest / deepeval test run                    python -m kerimbalci_com.evals
 assert_test → Confident AI                    run_suite (EVAL_CONCURRENCY paralel)
                                               → özet tablo + reports/*.json

Her iki yol da aynı suite tanımını (evals/suites/factuality_suite.py) kullanır.
```

## Sorumluluk ayrımı

- **Veri** (`dataset/`) ve **kriter** (`judges/`) koddan
  ayrıdır; soru veya kriter değiştirmek için Python dosyası düzenlenmez.
- `src/` tekrar kullanılabilir mantığı, `tests/` doğrulamayı içerir.
