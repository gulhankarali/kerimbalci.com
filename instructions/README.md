# Proje Talimatları — İçindekiler

Bu klasör kerimbalci.com chatbot değerlendirme (eval) projesinin
dokümantasyonudur. Hem projeye katkı yapan kişiler hem de Claude Code gibi
AI asistanlar için yazılmıştır. Temel kurallar kök dizindeki `CLAUDE.md`'de
özetlenir; ayrıntılar buradadır.

| Dosya | Konu |
|---|---|
| [setup.md](setup.md) | Sıfırdan kurulum ve ilk çalıştırma |
| [configuration.md](configuration.md) | Ortam değişkenleri, `.env`, `Settings` |
| [project-structure.md](project-structure.md) | Klasör ve modül yapısı |
| [project-rules.md](project-rules.md) | Kodlama kuralları ve konvansiyonlar |
| [testing.md](testing.md) | Test türleri, marker'lar, çalıştırma |
| [debugging.md](debugging.md) | Loglama ve VS Code debug |
| [deepeval.md](deepeval.md) | deepeval, hakem model, Confident AI |
| [chatbot.md](chatbot.md) | Chatbot istemcisi ve beklenen davranış |
| [dataset.md](dataset.md) | Eval dataset'lerinin hazırlanması |
| [../judges/factuality_judge/](../judges/factuality_judge/README.md) | Hakem (LLM-as-judge) YAML'ları — seviye 1-3 |
| [git.md](git.md) | Git akışı ve commit kuralları |

## Hızlı başlangıç

```bash
cp .env.example .env        # gerçek değerleri doldur
uv sync                     # bağımlılıkları kur
uv run pytest -m "not integration"   # hızlı, ücretsiz testler
uv run python -m kerimbalci_com.evals factuality --limit 3   # küçük eval denemesi (ücretli)
```
