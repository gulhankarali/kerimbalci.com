# Setup

## Requirements

- [uv](https://docs.astral.sh/uv/) (0.13+). uv also manages Python; you do not
  need to install Python separately.
- The Python version is in `.python-version` (3.11).
- Credentials: Hugging Face token, Anthropic API key, (optional) Confident AI
  project key.

## Steps

```bash
git clone <repo-url> && cd kerimbalci.com
uv sync                      # creates .venv, installs the versions from uv.lock
cp .env.example .env         # copy the template
# replace the example values in .env with real ones (see configuration.md)
```

## Verifying the setup

```bash
uv run pytest -m "not integration"   # unit tests — no network/API needed
uv run pytest -m integration -k "not eval" tests/integration/test_connections.py
                                     # HF Space, HF token, Anthropic key, JUDGE_MODEL
uv run python -m kerimbalci_com      # writes the application start log
```

The `tests/integration/` tests are **skipped**, not failed, when their variable
is not set. Make sure they all show `PASSED`.

## Notes

- `pip install` and `python -m venv` are not used; everything goes through `uv`.
- VS Code uses the `.venv` interpreter and the `.env` file automatically thanks
  to `.vscode/settings.json`.
