# Project Structure

```
kerimbalci.com/
├── CLAUDE.md                 # Core rules (Claude Code reads it every session)
├── pyproject.toml            # Project, dependencies, pytest settings
├── uv.lock                   # Pinned dependency versions (committed)
├── .env.example              # Environment variable template (committed)
├── .env                      # Real values (NOT COMMITTED)
├── .cache/                   # Crawled site texts, generated raw JSON (NOT COMMITTED)
├── reports/                  # Runner JSON reports (NOT COMMITTED)
├── .vscode/                  # launch.json (F5 debugging), settings.json
├── .github/workflows/        # ci.yml (unit tests), eval.yml (manual, paid eval)
├── instructions/             # This documentation
├── dataset/
│   ├── factuality/           # Factuality eval dataset (4 categories, JSON)
│   └── hallucination/        # Hallucination eval dataset (4 categories, 50 records)
├── judges/
│   ├── factuality_judge/     # Judge YAMLs: level1_basic, level2_intermediate, level3_advanced
│   ├── hallucination_judge/  # Hallucination judges (same 3 levels)
│   └── expected_behavior_judge/  # Behavior judge (language, concision, tone, framing)
├── src/kerimbalci_com/
│   ├── __init__.py           # main(): loads settings, sets up logging
│   ├── __main__.py           # python -m kerimbalci_com entry point
│   ├── config.py             # Settings, get_settings(), setup_logging()
│   ├── chatbot.py            # ChatbotClient — sends questions to the HF Space
│   ├── datasets.py           # DatasetSchema, load_factuality(), load_hallucination()
│   ├── dataset_builder/      # Dataset generation from the site: crawl, split, merge, verify (python -m ...)
│   └── evals/
│       ├── __main__.py       # CLI: python -m kerimbalci_com.evals <suite> [--tags/--ids/--limit/--level]
│       ├── eval_suite.py     # EvalSuite: cases + metric factory + filter
│       ├── suite_runner.py   # run_suite(): parallel runs, CaseResult/SuiteResult
│       ├── judge_config.py   # JudgeSet, load_judge() (YAML) + build_geval()
│       ├── reporter.py       # Per-tag summary table + JSON report (reports/)
│       ├── compare.py        # Compares two reports: regressed/fixed cases
│       └── suites/
│           ├── __init__.py            # SUITES registry
│           ├── common.py              # Shared: LLMTestCase + metric factory
│           ├── factuality_suite.py    # dataset/factuality + judges/factuality_judge
│           └── hallucination_suite.py # dataset/hallucination + judges/hallucination_judge
└── tests/
    ├── conftest.py           # Shared fixtures: settings, chatbot, judge_model
    ├── unit/                 # No network/API
    │   ├── test_config.py    # Settings
    │   ├── test_datasets.py  # Dataset schemas + real datasets
    │   ├── test_judges.py    # Judge YAML schema
    │   ├── test_dataset_builder.py  # Crawling, text extraction, merge (fake fetch)
    │   ├── test_dataset_verify.py   # Verifying evidence quotes against the site text
    │   ├── test_chatbot.py   # Timeout / retry (fake Gradio)
    │   ├── test_compare.py   # Report comparison
    │   └── test_evals.py     # Suites, runner, reporter, CLI (fake chatbot/judge)
    ├── integration/
    │   └── test_connections.py  # HF Space, HF token, Anthropic, JUDGE_MODEL
    ├── factuality/
    │   └── test_factuality.py   # Eval: the factuality suite via pytest/deepeval
    └── hallucination/
        └── test_hallucination.py  # Eval: the hallucination suite via pytest/deepeval
```

## Data flow (eval)

```
dataset/<suite>/*.json ──load_<suite>()──┐
                                         ▼
                   ChatbotClient.ask(input) → actual_output
                                         ▼
judges/<suite>_judge/level<N>.yaml ──load_judge()/build_geval()──► GEval (judge: JUDGE_MODEL)
  (N = <SUITE>_JUDGE_LEVEL; evidence → context)
                                         ▼
      ┌──────────────────────────┴──────────────────────────┐
      ▼                                                     ▼
 pytest / deepeval test run                    python -m kerimbalci_com.evals
 assert_test → Confident AI                    run_suite (EVAL_CONCURRENCY in parallel)
                                               → summary table + reports/*.json

Both paths use the same suite definition (evals/suites/<suite>_suite.py).
```

## Separation of concerns

- **Data** (`dataset/`) and **criteria** (`judges/`) are separate from code;
  changing a question or a criterion does not require editing a Python file.
- `src/` holds reusable logic, `tests/` holds verification.
