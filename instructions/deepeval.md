# deepeval and Confident AI

## Concepts
- **LLMTestCase:** `input` (question), `actual_output` (chatbot answer),
  `expected_output` (the correct answer from the dataset). In the eval suites
  `name` = record id, `tags` = category, `context` = the record's `evidence`.
- **Metric:** scores the answer between 0 and 1; below `threshold` = failure.
  - `GEval` — a judge score based on criteria written in natural language. In
    the factuality and hallucination suites every case is measured with two
    GEvals: the suite's main metric (**Factuality**: are the facts right? /
    **Hallucination**: was anything invented?) and **Expected Behavior**
    (language, concision, tone, framing — `judges/expected_behavior_judge/`,
    `EVAL_EXPECTED_BEHAVIOR`). A case passes only if both pass; the report also
    gives a per-metric summary.
    Criteria come from `judges/<suite>_judge/*.yaml` (levels 1-3,
    `FACTUALITY_JUDGE_LEVEL` / `HALLUCINATION_JUDGE_LEVEL`). `evaluation_steps` +
    `rules` + `rubric` (0-10 score bands) are passed to GEval.
- **Judge:** the LLM doing the scoring; `AnthropicModel(model=JUDGE_MODEL)`.
- **assert_test:** runs the metrics and fails the test when below the threshold.

## Running

```bash
uv run deepeval test run tests/factuality/   # recommended: summary table + Confident AI
uv run pytest -m eval tests/factuality/      # plain pytest
HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fab-001   # hallucination
```

`deepeval test run` shows a per-metric summary table at the end and uploads the
results to Confident AI when `CONFIDENT_API_KEY` is set.

## Our own runner

`src/kerimbalci_com/evals/` runs the deepeval metrics directly with
`metric.measure()` in a thread pool (`EVAL_CONCURRENCY`), so suite metrics are
built with `async_mode=False`. Results are **not** sent to Confident AI; JSON
is written under `reports/`. To add a new suite, write
`build_suite(settings, judge_model)` in `evals/suites/<name>_suite.py` and add it
to `evals/suites/__init__.py` → `SUITES`.

## Confident AI
- app.confident-ai.com → project → Settings → Project API Key →
  `CONFIDENT_API_KEY` in `.env`.
- Every run shows up as a "test run"; records can be filtered by id and
  category tag, and runs can be compared.
- The `.deepeval/` folder is deepeval's local cache/settings.

## Cost
- Each test case = 1 chatbot call + judge calls (GEval step generation and
  scoring). The 100-record factuality set makes hundreds of judge requests.
- Try small runs first with `-k <category>` or `-k <id>`.
- Runner reports show the judge cost: below the summary table
  `Judge cost: $X, per case $Y (input / output tokens)`; in the JSON
  `summary.overall.usage`, per tag `summary.by_tag.<tag>.usage`, per case
  `cases[].usage`. `compare` also prints the cost difference of two runs.
- Prices come from deepeval's model table. If it is out of date, add
  `ANTHROPIC_COST_PER_INPUT_TOKEN` / `ANTHROPIC_COST_PER_OUTPUT_TOKEN`
  (USD per token) to `.env`; deepeval reads them itself.
- The chatbot (HF Space) cost is not included in the report.

## Changing criteria
Edit the relevant YAML under `judges/<suite>_judge/` →
`uv run pytest tests/unit/test_judges.py` → try a few records → compare with
the previous run in Confident AI.
