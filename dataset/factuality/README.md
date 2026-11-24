# Factuality Dataset

Question-answer sets (100 records) that measure whether the chatbot gives
**correct information** about kerimbalci.com. Source: the **whole** site — 52
articles, 9 pages and 10 series/tag pages from the sitemap (as of 2026-11-23).
The questions are spread over 68 different pages; at most 3 questions per page.

Each record's `evidence` field is a **verbatim quote** from the source page and
was verified automatically against the page text when it was created. For paid
articles only the public part before the paywall was used.

The questions, expected answers and evidence are in Turkish on purpose: the
chatbot answers a Turkish site in Turkish.

| File | What it measures |
|---|---|
| `direct_facts.json` | Fact questions with a single correct answer (biography, membership). |
| `false_premise.json` | Questions containing false information; the chatbot must **correct** the premise, not accept it. |
| `unanswerable.json` | Questions whose answer is not on the site; the chatbot must **not invent** and should say it does not know. |
| `time_sensitive.json` | Information that may change; re-verify after the `valid_as_of` date. |

## Record schema

```json
{
  "id": "fact-001",                 // required, unique across all files
  "input": "Question",              // required
  "expected_output": "Expected",    // required
  "category": "direct_fact",        // required: direct_fact | false_premise | unanswerable | time_sensitive
  "source_url": "https://...",      // source page (may be null for generic unanswerable records)
  "evidence": "...",                // verbatim quote from the source page (evidence)
  "false_claim": "...",             // required for false_premise
  "valid_as_of": "2026-11-23",      // required for time_sensitive
  "notes": "..."                    // optional
}
```

The `input` / `expected_output` fields map directly to deepeval's `Golden`.
The structure is validated by `tests/unit/test_datasets.py` (`uv run pytest tests/unit/test_datasets.py`).

## Evaluating the chatbot with this set

```bash
uv run deepeval test run tests/factuality/           # all (paid: 100 judge requests)
uv run pytest -m eval tests/factuality/ -k unanswerable   # one category
```

Each category is scored with its own judge criteria (see `judges/factuality_judge/`).
Judge: `judges/factuality_judge/` (level from `.env` → `FACTUALITY_JUDGE_LEVEL`).
Threshold: `threshold` from the YAML; `.env` → `EVAL_FACTUALITY_THRESHOLD` if set.

## Maintenance

`time_sensitive` records (latest post, membership content, print plans) go
stale as the site is updated; re-verify them periodically based on their
`valid_as_of` date. To check all evidence quotes against the site text:
`uv run python -m kerimbalci_com.dataset_builder verify factuality`.
