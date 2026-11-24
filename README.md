# kerimbalci.com — Chatbot Eval Automation

An LLM eval framework that measures the quality of the chatbot (a Hugging Face
Space) that answers questions about [kerimbalci.com](https://kerimbalci.com).
The chatbot is asked the questions in the dataset, the answers are scored by a
judge model (LLM-as-judge, Anthropic) with [deepeval](https://deepeval.com),
and the results are written to Confident AI or to a local JSON report.

## Quick start

```bash
uv sync                                   # dependencies
cp .env.example .env                      # fill in the real values
uv run pytest -m "not integration"        # unit tests (free)
uv run pytest -m "integration and not eval"   # connection check
uv run python -m kerimbalci_com.evals factuality --limit 3   # small eval (paid)
```

## Structure

| Folder | Contents |
|---|---|
| `dataset/factuality/` | 100 question-answer pairs (4 categories), each with a verbatim quote from the site |
| `dataset/hallucination/` | 50 hallucination trap questions (4 categories), each with a verbatim quote from the site |
| `judges/` | Judge definitions (YAML): `factuality_judge/`, `hallucination_judge/` (level 1-3) + `expected_behavior_judge/` (language, tone, concision) |
| `src/kerimbalci_com/evals/` | Suites, parallel runner, judge setup, reporting, CLI |
| `src/kerimbalci_com/dataset_builder/` | Dataset generation from the site: crawl → split → merge → verify |
| `tests/` | `unit/`, `integration/`, `factuality/` and `hallucination/` (eval) + `conftest.py` |
| `.github/workflows/` | `ci.yml`: unit tests on every push · `eval.yml`: manually triggered eval |
| `instructions/` | Documentation — setup, configuration, testing, debugging, deepeval, git |

The dataset questions, expected answers and evidence quotes are in Turkish on
purpose: the chatbot answers a Turkish site in Turkish.

## Running evals

```bash
# pytest path that uploads to Confident AI
uv run deepeval test run tests/factuality/
uv run pytest -m eval tests/factuality/ -k false_premise
HALLUCINATION_JUDGE_LEVEL=1 uv run pytest tests/hallucination -m eval -k fake_attribution

# Parallel runner with local reports (reports/*.json)
uv run python -m kerimbalci_com.evals factuality --tags unanswerable --level 3

# Compare two runs: regressed / fixed cases
uv run python -m kerimbalci_com.evals.compare
```

The judge level (`FACTUALITY_JUDGE_LEVEL` / `HALLUCINATION_JUDGE_LEVEL`),
concurrency (`EVAL_CONCURRENCY`) and quality gate (`EVAL_MIN_PASS_RATE`; the
runner exits with 1 when the pass rate is below it) are set in `.env`. All
variables: [instructions/configuration.md](instructions/configuration.md).

> Eval tests make paid API requests for the judge model; try a small subset first.

More details: [instructions/README.md](instructions/README.md)
