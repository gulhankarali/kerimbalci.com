# kerimbalci.com — Chatbot Eval Otomasyonu

[kerimbalci.com](https://kerimbalci.com) sitesi hakkında soru cevaplayan
chatbot'un (Hugging Face Space) kalitesini ölçen LLM eval framework'ü.
Chatbot'a dataset'teki sorular sorulur, cevaplar bir hakem model
(LLM-as-judge, Anthropic) tarafından [deepeval](https://deepeval.com) ile
puanlanır; sonuçlar Confident AI'ya veya yerel JSON rapora yazılır.

## Hızlı başlangıç

```bash
uv sync                                   # bağımlılıklar
cp .env.example .env                      # gerçek değerleri doldur
uv run pytest -m "not integration"        # birim testler (ücretsiz)
uv run pytest -m "integration and not eval"   # bağlantı kontrolü
uv run python -m kerimbalci_com.evals factuality --limit 3   # küçük eval (ücretli)
```

## Yapı

| Klasör | İçerik |
|---|---|
| `dataset/factuality/` | 100 soru-cevap (4 kategori), her biri siteden birebir kanıtlı |
| `dataset/hallucination/` | 50 uydurma tuzağı sorusu (4 kategori), her biri siteden birebir kanıtlı |
| `judges/` | Hakem tanımları (YAML): `factuality_judge/`, `hallucination_judge/` (level 1-3) + `expected_behavior_judge/` (dil, ton, kısalık) |
| `src/kerimbalci_com/evals/` | Suite, paralel runner, hakem kurulumu, raporlama, CLI |
| `src/kerimbalci_com/dataset_builder/` | Siteden dataset üretimi: crawl → split → merge |
| `tests/` | `unit/`, `integration/`, `factuality/` ve `hallucination/` (eval) + `conftest.py` |
| `.github/workflows/` | `ci.yml`: her push'ta birim testler · `eval.yml`: elle tetiklenen eval |
| `instructions/` | Dokümantasyon — kurulum, yapılandırma, test, debug, deepeval, git |

## Eval çalıştırma

```bash
# Confident AI'ya yükleyen pytest yolu
uv run deepeval test run tests/factuality/
uv run pytest -m eval tests/factuality/ -k false_premise
HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fake_attribution

# Paralel, yerel raporlu runner (reports/*.json)
uv run python -m kerimbalci_com.evals factuality --tags unanswerable --level 3

# İki koşuyu karşılaştır: bozulan / düzelen case'ler
uv run python -m kerimbalci_com.evals.compare
```

Hakem seviyesi `FACTUALITY_JUDGE_LEVEL` / `HALLUCINATION_JUDGE_LEVEL`, eşzamanlılık `EVAL_CONCURRENCY`,
kalite kapısı `EVAL_MIN_PASS_RATE` (runner geçen oran bunun altındaysa 1 ile
çıkar) `.env`'den ayarlanır. Tüm değişkenler: [instructions/configuration.md](instructions/configuration.md).

> Eval testleri hakem model için ücretli API istekleri atar; önce küçük bir
> alt kümede deneyin.

Ayrıntılar için: [instructions/README.md](instructions/README.md)
