# Hallucination Dataset

50 golden records that measure whether the chatbot **invents something that is
not on kerimbalci.com**. Factuality asks "is the answer right?"; hallucination
asks "was something without support on the site added to the answer?". Each
question is designed to lure the chatbot into a known hallucination trap.

Each record's `evidence` field is a **verbatim quote** from the source page and
is verified automatically (`dataset_builder verify hallucination`). Care was
taken not to overlap with the `false_premise` / `unanswerable` questions of the
factuality set. Questions, expected answers and evidence are in Turkish on
purpose: the chatbot answers a Turkish site in Turkish.

| File | Category | Records | What it measures |
|---|---|---|---|
| `fabricated_detail.json` | `fabricated_detail` | 14 | The topic is on the site, the requested detail is not (book titles, TV channel, amount, thesis title…). The chatbot should say "not on the site" and give what the site does say. |
| `fake_attribution.json` | `fake_attribution` | 12 | A statement/idea is attributed to the wrong person (Pericles, Tanpınar, Avi, his mother…) or was never said. The chatbot should name the right person or say the statement is not on the site. |
| `entity_confusion.json` | `entity_confusion` | 12 | Two similar entities on the site (Durham/Burch, ICJ/ICC, Avi/Yael…). Properties must be assigned to the right entity. |
| `unsupported_addition.json` | `unsupported_addition` | 12 | The answer is on the site; the risk is unsupported additions from general knowledge (dates, names, definitions). The chatbot should stay within what the site says. |

## Record schema

```json
{
  "id": "fab-001",                  // required, unique (fab | attr | conf | add)
  "input": "Question",              // required
  "expected_output": "Expected",    // required; relies only on the site content
  "category": "fabricated_detail",  // required: one of the 4 categories above
  "hallucination_trap": "...",      // required: what the chatbot is tempted to invent
  "source_url": "https://...",      // required: source page
  "evidence": "..."                 // required: verbatim quote from the source page (→ LLMTestCase.context)
}
```

`hallucination_trap` is given to the Level 3 judge through the
`{hallucination_trap}` placeholder; the judge additionally checks whether the
answer fell into this trap. The schema is defined in
`src/kerimbalci_com/datasets.py` → `HALLUCINATION` and validated by
`tests/unit/test_datasets.py`.

## Running

```bash
HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fab-001    # one record
uv run pytest -m eval tests/hallucination/ -k fake_attribution                      # one category
uv run deepeval test run tests/hallucination/                                       # all (paid)
uv run python -m kerimbalci_com.evals hallucination --limit 3                       # parallel runner
```

Judge: `judges/hallucination_judge/` (level from `.env` → `HALLUCINATION_JUDGE_LEVEL`).
Threshold: `threshold` from the YAML; `.env` → `EVAL_HALLUCINATION_THRESHOLD` if set.

## Maintenance

Verify the quotes before adding or changing records:

```bash
uv run python -m kerimbalci_com.dataset_builder verify hallucination
```

`fabricated_detail` and `fake_attribution` records rely on a "not on the site"
claim; as the site is updated, check that this information is still not on the site.
