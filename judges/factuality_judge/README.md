# Factuality Judge

deepeval `GEval` hakem yapılandırmaları. Kod kriter içermez; hakem bu YAML
dosyalarından kurulur (`src/kerimbalci_com/evals/judge_config.py` → `load_judge`, `build_geval`).

| Seviye | Dosya | Ne kontrol eder? | context |
|---|---|---|---|
| 1 | `factuality_judge_level1_basic.yaml` | Temel olgu doğru mu? | Hayır |
| 2 | `factuality_judge_level2_intermediate.yaml` | + uydurma ayrıntı, eksik kilit olgu | `evidence` |
| 3 | `factuality_judge_level3_advanced.yaml` | + kategoriye özel davranış (yanlış öncül, cevapsız, zamana bağlı) | `evidence` |

Seçim: `.env` → `FACTUALITY_JUDGE_LEVEL=1|2|3` (varsayılan 3).
Eşik: YAML'daki `threshold`; `.env` → `EVAL_FACTUALITY_THRESHOLD` doluysa onu ezer.

## Şema

| Alan | Zorunlu | GEval karşılığı |
|---|---|---|
| `name`, `level`, `description` | Evet | `name` |
| `threshold` (0-1) | Evet | `threshold` |
| `evaluation_params` | Evet | `input`, `actual_output`, `expected_output`, `context` |
| `criteria` | Evet | Dokümantasyon; `evaluation_steps` verildiği için GEval adımları kullanır |
| `evaluation_steps` | Evet | `evaluation_steps` (ilk kısım) |
| `rules` | Hayır | `"Rule: ..."` olarak adımlara eklenir |
| `category_steps` | Hayır | Kaydın kategorisine ait adımlar en sona eklenir |
| `rubric` | Evet | `Rubric(score_range, expected_outcome)`; aralıklar 0-10'u boşluksuz, çakışmasız kapsar |

Kanıtı (`evidence`) olmayan kayıtlarda `context` parametresi otomatik çıkarılır.

## Değiştirme
YAML'ı düzenleyin → `uv run pytest tests/unit/test_judges.py` (şema) →
`uv run pytest -m eval tests/factuality/ -k <kategori>` ile küçük deneme.
