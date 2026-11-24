# Debugging

## Logging
- No `print()`; every module has `logger = logging.getLogger(__name__)`.
- With `.env` → `DEBUG=true`, `setup_logging()` sets the level to DEBUG
  automatically; otherwise `LOG_LEVEL` is used.
- pytest live logging is on (`log_cli = true`, INFO). For more detail:
  `uv run pytest --log-cli-level=DEBUG ...`
- `ChatbotClient.ask` logs the question and the first 200 characters of the
  answer at DEBUG level — useful to see what the chatbot returned during an eval.

## VS Code (F5)

`.vscode/launch.json` contains three configurations; all of them load `.env`:

| Configuration | What it does |
|---|---|
| Python: Debug the App | `python -m kerimbalci_com` |
| Python: Debug Current File | Runs the file open in the editor |
| Pytest: Debug Tests | Runs pytest under the debugger (`justMyCode: false`) |

To debug a single eval record, temporarily set the `args` of the Pytest
configuration to `["-v", "tests/factuality/", "-k", "fact-001"]` (do not commit it).

## Common issues

| Symptom | Likely cause |
|---|---|
| Tests `SKIPPED` | The variable is missing from `.env` (`HF_CHATBOT_URL`, `JUDGE_MODEL` …) |
| `DatasetError` | Missing field / duplicate id in a dataset JSON — the message shows the record |
| `JudgeConfigError` | A judge YAML does not match the schema (missing field, rubric gap/overlap) — the message shows the file |
| Empty chatbot answer | The Space may be sleeping; check with `test_hf_chatbot_space_is_reachable` |
| `ChatbotError: ... failed after N attempts` | The Space does not respond; increase `CHATBOT_TIMEOUT` / `CHATBOT_MAX_RETRIES`, the logs show the error of every attempt |
| Runner exit code 1 | The quality gate failed (pass rate < `EVAL_MIN_PASS_RATE`); look at the `passed: false` cases in `reports/*.json` |
| Judge 401/404 | `ANTHROPIC_API_KEY` or `JUDGE_MODEL` is wrong — `test_connections.py` |
