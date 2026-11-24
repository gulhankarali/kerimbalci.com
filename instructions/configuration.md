# Dynamic Configuration (No Hardcoding)

No setting, path, URL, key or threshold is hardcoded in the code. Flow:

```
.env  →  python-dotenv (when config.py is loaded)  →  Settings  →  get_settings()
```

`src/kerimbalci_com/config.py` finds the project root with `Path(__file__)` and
loads `.env` from there. Every call to `get_settings()` builds a new `Settings`
from the **current environment** (this is what makes `monkeypatch` work in tests).
Precedence: **system environment variable > `.env` > default in code**.

## Variables

| Variable | Read by | Description |
|---|---|---|
| `APP_NAME` | `Settings.app_name` | Application / logger name |
| `ENVIRONMENT` | `Settings.environment` | `development` \| `staging` \| `production` |
| `DEBUG` | `Settings.debug` | When `true`, the log level is automatically DEBUG |
| `LOG_LEVEL` | `Settings.log_level` | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `JUDGE_MODEL` | `Settings.judge_model` | Anthropic model used as the judge |
| `HF_CHATBOT_URL` | `Settings.hf_chatbot_url` | HF Space URL of the chatbot under test |
| `CHATBOT_API_ENDPOINT` | `Settings.chatbot_endpoint` | Gradio endpoint (default `/cevapla`) |
| `HF_TOKEN` | `Settings.hf_token` | Hugging Face token (secret) |
| `CHATBOT_TIMEOUT` | `Settings.chatbot_timeout` | Timeout per question, s (default 60) |
| `CHATBOT_MAX_RETRIES` | `Settings.chatbot_max_retries` | Retries on error/timeout (default 2; 0 = off) |
| `CHATBOT_RETRY_BACKOFF` | `Settings.chatbot_retry_backoff` | Initial backoff, s; doubles on each attempt (default 2 → 2, 4, …) |
| `FACTUALITY_JUDGE_LEVEL` | `Settings.factuality_judge_level` | Factuality judge level: 1 basic, 2 intermediate, 3 advanced (default 3) |
| `EVAL_FACTUALITY_THRESHOLD` | `Settings.factuality_threshold` | Factuality threshold (0-1); if empty, the `threshold` from the judge YAML |
| `HALLUCINATION_JUDGE_LEVEL` | `Settings.hallucination_judge_level` | Hallucination judge level: 1 basic, 2 intermediate, 3 advanced (default 3) |
| `EVAL_HALLUCINATION_THRESHOLD` | `Settings.hallucination_threshold` | Hallucination threshold (0-1); if empty, the `threshold` from the judge YAML |
| `EVAL_EXPECTED_BEHAVIOR` | `Settings.eval_expected_behavior` | Second metric (behavior) in the factuality and hallucination suites; `false` = off (default `true`) |
| `EVAL_CONCURRENCY` | `Settings.eval_concurrency` | Cases running at the same time in the runner (default 4) |
| `EVAL_TAGS` | `Settings.eval_tags` | Runner runs only these tags (comma-separated; empty = all) |
| `EVAL_MIN_PASS_RATE` | `Settings.eval_min_pass_rate` | Runner quality gate: minimum pass rate (default 0.85) |
| `EVAL_COMPARE_MIN_DELTA` | `Settings.eval_compare_min_delta` | "Score changed" threshold in report comparison (default 0.2) |
| `EVAL_REPORT_DIR` | `Settings.eval_report_dir` | Folder for JSON reports, relative to the project root (default `reports`) |
| `ANTHROPIC_API_KEY` | Anthropic SDK / deepeval | Judge model API key (secret) |
| `CONFIDENT_API_KEY` | deepeval | Sends results to Confident AI (secret, optional) |
| `ANTHROPIC_COST_PER_INPUT_TOKEN` / `..._OUTPUT_TOKEN` | deepeval | Optional: judge price (USD per token); if empty, deepeval's table |
| `HTTP_TIMEOUT` | `Settings.http_timeout` | Timeout for external HTTP requests, s (default 30) |
| `SITE_URL` | `Settings.site_url` | Site crawled for datasets (default `https://kerimbalci.com`) |
| `SITE_WORKDIR` | `Settings.site_workdir` | Downloaded page texts, relative to the project root (default `.cache/site`, not in git) |
| `CRAWL_USER_AGENT` | `Settings.crawl_user_agent` | User-Agent header of crawl requests |

## Adding a new setting

1. Add it to `.env.example` with a comment line (no secret values).
2. Put the real value in your own `.env` file.
3. Add a field to `Settings`:
   `new_setting: str = field(default_factory=lambda: os.getenv("NEW_SETTING", "default"))`
4. Use it in code via `get_settings().new_setting`.
5. Add a default + read-from-environment test to `tests/unit/test_config.py`.
6. Add it to this table.

## GitHub Actions

There is no `.env` in CI; values are passed as environment variables
(repo → Settings → Secrets and variables → Actions):

| Type | Name |
|---|---|
| Secret | `HF_TOKEN`, `ANTHROPIC_API_KEY`, `CONFIDENT_API_KEY` (optional) |
| Variable | `HF_CHATBOT_URL`, `JUDGE_MODEL`, `CHATBOT_API_ENDPOINT` (optional) |

Other settings use the defaults in code; to change them, add them to
`.github/workflows/eval.yml` → `env:`.

## Secrets

- `.env` is never committed (it is in `.gitignore`). `.env.example` is
  committed and contains only example values.
- Secret values are never logged.
