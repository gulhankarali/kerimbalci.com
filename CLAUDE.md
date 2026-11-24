# Project Instructions

This file defines the working rules of the project. Everyone who contributes
(human or AI) follows these rules. Claude Code reads this file automatically at
the start of every session.

Project: LLM eval automation framework for the kerimbalci.com chatbot
(deepeval + Confident AI). Detailed documentation lives in the
**`instructions/`** folder (contents: `instructions/README.md`); read the
relevant file before working on a topic.

## 1. Toolchain

- Package/project management is done **only with `uv`**. Commands such as
  `pip install` or `python -m venv` are not used.
- The Python version is defined in `.python-version` (3.11).
- Tests are written with **pytest** and run with `uv run pytest`.

## 2. Dynamic Configuration — No Hardcoding

- **No setting, path, URL, key or constant is hardcoded.**
- All configuration is read from environment variables:
  `.env` → `python-dotenv` → `src/kerimbalci_com/config.py` → `Settings`.
- When a new setting is needed, the order is:
  1. Add a commented line to `.env.example` (with a default/example value),
  2. Put the real value in your own `.env` file,
  3. Add the field to the `Settings` class in `config.py`,
  4. Use it in code via `get_settings()`.
- File paths are computed dynamically from `Path(__file__)`; no absolute paths.

## 3. Environment Variables (.env)

- `.env` holds the real values and is **never committed to git** (it is in `.gitignore`).
- `.env.example` is the template; it contains no secrets and is committed.
- New setup: `cp .env.example .env`
- The full list of variables and their descriptions: `instructions/configuration.md`.
  When a new variable is added, that table is updated too.
- Secret keys (`HF_TOKEN`, `ANTHROPIC_API_KEY`, `CONFIDENT_API_KEY`) are never
  logged and never written into code or documentation.

## 4. Debugging

- With `DEBUG=true` in `.env`, the log level automatically becomes `DEBUG`
  and verbose logs are shown (`config.setup_logging`).
- Debug in VS Code with **F5**: `.vscode/launch.json` contains three configurations:
  - *Python: Debug the App* — starts the package with `python -m`,
  - *Python: Debug Current File* — runs the file open in the editor,
  - *Pytest: Debug Tests* — runs pytest under the debugger.
- All debug configurations load the `.env` file automatically.
- No debugging with `print()`; use `logging`.

## 5. Testing

- Every new module/function gets tests under `tests/`:
  - `tests/unit/` — tests without network/API (fake chatbot/judge),
  - `tests/integration/` — external service connection tests (`-m integration`),
  - `tests/<suite>/` — LLM eval tests (`-m eval`, **paid**).
- Shared fixtures are in `tests/conftest.py`; a test is skipped when a setting is missing.
- Eval tests are not run as a full set without permission; try a small subset
  with `-k` first.
- Environment variables in tests are set with `monkeypatch`; no test may depend
  on the real `.env` file.
- Quick check: `uv run pytest -m "not integration"`
  (settings in `pyproject.toml` → `[tool.pytest.ini_options]`).

## 6. Git

- The repository was created with `uv init`; secret and generated files are in `.gitignore`.
- `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.deepeval/`, `.cache/`,
  `reports/` are never committed.
- Make small, meaningful commits; the commit message summarizes the change
  (in English, imperative mood — see `instructions/git.md`).

## 7. Adding Dependencies

- Runtime dependency: `uv add <package>`
- Development dependency (tests, linting, etc.): `uv add --dev <package>`
- `uv.lock` is committed, so the environment is identical on every machine.

## 8. Data, Judges and Eval Structure

- **Data and criteria are separate from code:** questions live in
  `dataset/<suite>/*.json`, judge definitions in `judges/<suite>_judge/*.yaml`.
  Changing a question or a criterion does not require changing Python code.
- Dataset expected answers rely only on the site content; every record carries
  a verbatim `evidence` quote (`instructions/dataset.md`).
- Dataset questions, expected answers and evidence quotes stay in **Turkish**
  (the chatbot answers a Turkish site in Turkish); everything else in the repo
  is in English.
- Eval code is under `src/kerimbalci_com/evals/`: `EvalSuite` (suite definition),
  `suite_runner` (parallel runs), `judge_config` (YAML → GEval), `reporter`,
  `suites/<name>_suite.py`. New suite = new `suites/<name>_suite.py`
  + `SUITES` entry + `dataset/<name>/` + `judges/<name>_judge/` + `tests/<name>/`.
