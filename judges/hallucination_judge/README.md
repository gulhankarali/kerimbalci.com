# Hallucination Judge

deepeval `GEval` judge configurations. Uses the same schema as the factuality
judge (see `../factuality_judge/README.md`); the judge is built with
`judge_config.load_judge(level, judges=HALLUCINATION_JUDGES)`.

| Level | File | What it checks |
|---|---|---|
| 1 | `hallucination_judge_level1_basic.yaml` | Is there an **obvious** invention that neither the evidence nor the expected answer supports? |
| 2 | `hallucination_judge_level2_intermediate.yaml` | + claim-by-claim audit: hedged guesses, wrong attributions, additions from general knowledge |
| 3 | `hallucination_judge_level3_advanced.yaml` | + category-specific trap check (`{hallucination_trap}`) |

All three levels use `context` (= the record's `evidence` quote) and
`expected_output`; they differ in how deep the audit goes. Saying "this
information is not on the site" never counts as an invention at any level.

Selection: `.env` → `HALLUCINATION_JUDGE_LEVEL=1|2|3` (default 3).
Threshold: `threshold` from the YAML; `.env` → `EVAL_HALLUCINATION_THRESHOLD` overrides it if set.
Tone/style are ignored by this judge; `../expected_behavior_judge/` measures them
(`EVAL_EXPECTED_BEHAVIOR`).

`category_steps` keys may only be hallucination categories:
`fabricated_detail`, `fake_attribution`, `entity_confusion`, `unsupported_addition`.

## Changing it
Edit the YAML → `uv run pytest tests/unit/test_judges.py` (schema) →
try a small run with `HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k <category>`.
