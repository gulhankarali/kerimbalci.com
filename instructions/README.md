# Project Instructions — Contents

This folder is the documentation of the kerimbalci.com chatbot evaluation
(eval) project. It is written both for contributors and for AI assistants such
as Claude Code. The core rules are summarized in `CLAUDE.md` at the repository
root; the details are here.

| File | Topic |
|---|---|
| [setup.md](setup.md) | Setup from scratch and first run |
| [configuration.md](configuration.md) | Environment variables, `.env`, `Settings` |
| [project-structure.md](project-structure.md) | Folder and module structure |
| [project-rules.md](project-rules.md) | Coding rules and conventions |
| [testing.md](testing.md) | Test types, markers, running tests |
| [debugging.md](debugging.md) | Logging and VS Code debugging |
| [deepeval.md](deepeval.md) | deepeval, judge model, Confident AI |
| [chatbot.md](chatbot.md) | Chatbot client and expected behavior |
| [dataset.md](dataset.md) | Preparing the eval datasets |
| [../judges/factuality_judge/](../judges/factuality_judge/README.md) | Factuality judge (LLM-as-judge) YAMLs — levels 1-3 |
| [../judges/hallucination_judge/](../judges/hallucination_judge/README.md) | Hallucination judges — levels 1-3 |
| [../dataset/hallucination/](../dataset/hallucination/README.md) | Hallucination dataset — categories, schema, maintenance |
| [git.md](git.md) | Git workflow and commit rules |

## Quick start

```bash
cp .env.example .env        # fill in the real values
uv sync                     # install dependencies
uv run pytest -m "not integration"   # fast, free tests
uv run python -m kerimbalci_com.evals factuality --limit 3   # small eval trial (paid)
```
