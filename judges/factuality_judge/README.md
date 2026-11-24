# Factuality Judge

deepeval `GEval` judge configurations. The code contains no criteria; the judge
is built from these YAML files (`src/kerimbalci_com/evals/judge_config.py` →
`load_judge`, `build_geval`).

| Level | File | What it checks | context |
|---|---|---|---|
| 1 | `factuality_judge_level1_basic.yaml` | Is the core fact right? | No |
| 2 | `factuality_judge_level2_intermediate.yaml` | + invented details, missing key facts | `evidence` |
| 3 | `factuality_judge_level3_advanced.yaml` | + category-specific behavior (false premise, unanswerable, time-sensitive) | `evidence` |

Selection: `.env` → `FACTUALITY_JUDGE_LEVEL=1|2|3` (default 3).
Tone/style are deliberately ignored by this judge; `../expected_behavior_judge/` measures them.
Threshold: `threshold` from the YAML; `.env` → `EVAL_FACTUALITY_THRESHOLD` overrides it if set.

## Schema

| Field | Required | GEval equivalent |
|---|---|---|
| `name`, `level`, `description` | Yes | `name` |
| `threshold` (0-1) | Yes | `threshold` |
| `evaluation_params` | Yes | `input`, `actual_output`, `expected_output`, `context` |
| `criteria` | Yes | Documentation; since `evaluation_steps` are given, GEval uses the steps |
| `evaluation_steps` | Yes | `evaluation_steps` (first part) |
| `rules` | No | Appended to the steps as `"Rule: ..."` |
| `category_steps` | No | The steps for the record's category are appended at the end |
| `rubric` | Yes | `Rubric(score_range, expected_outcome)`; ranges cover 0-10 without gaps or overlaps |

For records without `evidence`, the `context` parameter is dropped automatically.

## Changing it
Edit the YAML → `uv run pytest tests/unit/test_judges.py` (schema) →
try a small run with `uv run pytest -m eval tests/factuality/ -k <category>`.
