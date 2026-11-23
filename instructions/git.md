# Git

## Ne commit edilir / edilmez

| Commit edilir | Asla commit edilmez |
|---|---|
| Kaynak kod, testler | `.env`, `.env.local`, `.env.*.local` |
| `pyproject.toml`, `uv.lock` | `.venv/` |
| `.env.example` | `__pycache__/`, `.pytest_cache/` |
| `dataset/`, `instructions/` | API anahtarı, token içeren her dosya |
| `.vscode/launch.json`, `settings.json` | `.DS_Store`, `.idea/` |
| `judges/` | `.deepeval/`, `.cache/`, `reports/` (üretilen dosyalar) |

Commit öncesi `git status` ile kontrol edin; gizli bilgi içeren dosya
listede olmamalı.

## Commit kuralları
- Küçük, tek konulu commit'ler: ör. dataset, eval testi ve dokümantasyon
  ayrı commit'ler.
- Mesaj değişikliği özetler, Türkçe, emir kipinde:
  `Factuality dataset'ini tüm siteden üret`,
  `Factuality hakem YAML'larını ekle`.
- Commit öncesi: `uv run pytest -m "not integration"` geçmeli.

## Akış

```bash
git status
uv run pytest -m "not integration"
git add <dosyalar>          # git add . yerine dosya dosya
git commit -m "Mesaj"
git push
```
