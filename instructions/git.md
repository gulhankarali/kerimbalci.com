# Git

## What is / is not committed

| Committed | Never committed |
|---|---|
| Source code, tests | `.env`, `.env.local`, `.env.*.local` |
| `pyproject.toml`, `uv.lock` | `.venv/` |
| `.env.example` | `__pycache__/`, `.pytest_cache/` |
| `dataset/`, `instructions/` | Any file containing an API key or token |
| `.vscode/launch.json`, `settings.json` | `.DS_Store`, `.idea/` |
| `judges/` | `.deepeval/`, `.cache/`, `reports/` (generated files) |

Check with `git status` before committing; no file with secrets may be in the list.

## Commit rules
- Small, single-topic commits: e.g. dataset, eval test and documentation in
  separate commits.
- The message summarizes the change, in English, in the imperative mood:
  `Generate the factuality dataset from the whole site`,
  `Add the factuality judge YAMLs`.
- Before committing: `uv run pytest -m "not integration"` must pass.

## Workflow

```bash
git status
uv run pytest -m "not integration"
git add <files>             # file by file instead of git add .
git commit -m "Message"
git push
```
