# Testing

Tests are written with pytest; settings are in `pyproject.toml` →
`[tool.pytest.ini_options]` (`-v --strict-markers`, live log INFO).

## Test types

| Type | Marker | Network/API | Cost | Files |
|---|---|---|---|---|
| Unit | — | No | None | `tests/unit/` |
| Connection | `integration` | Yes | None | `tests/integration/` |
| Eval | `integration` + `eval` | Yes | **Paid** (judge model) | `tests/<suite>/` (e.g. `tests/factuality/`) |

Shared fixtures (`settings`, `chatbot`, `judge_model`) are in `tests/conftest.py`;
they skip the test when a setting is missing. For a new suite create
`tests/<suite>/test_<suite>.py`.

Because `--strict-markers` is on, a new marker must be added to `pyproject.toml` first.

## Running

```bash
uv run pytest                              # everything (including evals — paid!)
uv run pytest -m "not integration"         # unit tests only (fast, free)
uv run pytest -m "integration and not eval"   # connection tests
uv run deepeval test run tests/factuality/   # factuality eval (100 questions)
uv run pytest -m eval tests/factuality/ -k unanswerable   # one category
uv run pytest -m eval tests/factuality/ -k "fact-001"               # one record
HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fab-001   # hallucination, one record
uv run deepeval test run tests/hallucination/   # hallucination eval (50 questions)
```

Try eval tests on a small subset with `-k` first.

### Runner (outside pytest, parallel)

```bash
uv run python -m kerimbalci_com.evals factuality --limit 3          # smoke test
uv run python -m kerimbalci_com.evals factuality --tags unanswerable --level 3
uv run python -m kerimbalci_com.evals factuality --ids fact-001,premise-002
uv run python -m kerimbalci_com.evals hallucination --tags entity_confusion --level 1
```

At the end it prints a per-tag summary table and writes
`reports/<suite>-L<N>-<timestamp>.json` (not in git).

**Quality gate:** the run fails when the pass rate is below `EVAL_MIN_PASS_RATE`
(default 0.85) or `--min-pass-rate`. Errored cases count as failures. The result
is on the last line of the summary table and under `summary.quality_gate` in the JSON.

Exit code: 0 gate passed, 1 gate failed, 2 missing setting / no case matches the filter.

### Comparing runs (regressions)

```bash
uv run python -m kerimbalci_com.evals.compare                    # last two reports of the same suite
uv run python -m kerimbalci_com.evals.compare --suite factuality-L3
uv run python -m kerimbalci_com.evals.compare reports/a.json reports/b.json
```

It lists the per-tag pass rate and average score difference, **regressed**
(passed → failed) and **fixed** (failed → passed) cases, and cases whose status
stayed the same but whose score changed by at least `EVAL_COMPARE_MIN_DELTA`
(default 0.2). It warns when different suites/judge levels are compared. Exit
code: 0 no regression, 1 regression, 2 no reports. Run with the same filter
before and after a chatbot or judge change and compare.

## CI (GitHub Actions)

| Workflow | Trigger | What it does | Cost |
|---|---|---|---|
| `.github/workflows/ci.yml` | Every push (main) and PR | `uv sync --locked` + `pytest -m "not integration"` | None |
| `.github/workflows/eval.yml` | Manual: Actions → Eval → Run workflow | Connection tests + runner (pick suite, level, tags, limit, threshold); `reports/` is kept as an artifact for 90 days | **Paid** |

Secrets/variables needed for the eval workflow: `configuration.md` → GitHub Actions.
To compare two CI runs, download the artifacts and give `compare` the two file paths.
The pytest path uploads to Confident AI; the runner is local and parallel.

## Rules
- Environment variables are set with `monkeypatch.setenv/delenv`.
- If a required variable is missing, the test is skipped with `pytest.skip(...)`.
- Unit tests that need files use `tmp_path`.
- The real datasets and judge YAMLs also have unit tests, so the fast tests
  catch it when these files break.
