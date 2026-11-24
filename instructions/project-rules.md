# Project Rules

The core rules are in `CLAUDE.md`; this file details them. If they conflict,
`CLAUDE.md` wins.

## Tools
- Package management only with `uv`: `uv add <package>`, `uv add --dev <package>`,
  `uv run <command>`. No `pip`/`venv`.
- `deepeval`, `anthropic`, `gradio-client`, `python-dotenv`, `pyyaml` are
  runtime dependencies (used by `src/kerimbalci_com/evals`); `pytest` is in the dev group.

## Code
- **No hardcoding:** settings, URLs, keys, thresholds, paths → `.env` + `Settings`
  (see `configuration.md`). Paths are based on `PROJECT_ROOT` / `Path(__file__)`.
- **Data and prompts are separate from code:** questions live under `dataset/`,
  judge criteria in the YAML files under `judges/`.
- No `print()`; `logger = logging.getLogger(__name__)` at the top of the module.
- Comments, docstrings, log and error messages in Python files are in English.
  Dataset content (questions, expected answers, evidence) stays in Turkish.
- Use type hints (`str | None`); short docstrings on functions.
- On errors, raise a custom exception with a meaningful message (e.g. `DatasetError`).

## Tests
- Tests under `tests/` for every new module/function.
- Environment variables via `monkeypatch`; no unit test depends on the real `.env`.
- Tests that need the network carry the `integration` marker; tests that make
  paid LLM calls also carry `eval`. A missing setting makes the test `skip`, not fail.

## Dataset
- Expected answers rely only on the site content; every record has `evidence`
  (see `dataset.md`).

## Git
- See `git.md`. `.env` and generated files are never committed.
