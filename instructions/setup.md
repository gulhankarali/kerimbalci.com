# Kurulum

## Gereksinimler

- [uv](https://docs.astral.sh/uv/) (0.13+). Python'u da uv yönetir;
  ayrıca Python kurmanız gerekmez.
- Python sürümü `.python-version` dosyasındadır (3.11).
- Erişim bilgileri: Hugging Face token, Anthropic API anahtarı, (opsiyonel)
  Confident AI proje anahtarı.

## Adımlar

```bash
git clone <depo-adresi> && cd kerimbalci.com
uv sync                      # .venv oluşturur, uv.lock'taki sürümleri kurar
cp .env.example .env         # şablonu kopyala
# .env içindeki örnek değerleri gerçek değerlerle değiştir (bkz. configuration.md)
```

## Kurulumu doğrulama

```bash
uv run pytest -m "not integration"   # birim testler — ağ/API gerektirmez
uv run pytest -m integration -k "not eval" tests/integration/test_connections.py
                                     # HF Space, HF token, Anthropic anahtarı, JUDGE_MODEL
uv run python -m kerimbalci_com      # uygulama başlangıç logunu yazar
```

`tests/integration/` testleri ilgili değişken tanımlı değilse **atlanır**
(skip), başarısız olmaz. Hepsinin `PASSED` olduğunu görün.

## Notlar

- `pip install` veya `python -m venv` kullanılmaz; her şey `uv` ile.
- VS Code, `.vscode/settings.json` sayesinde `.venv` yorumlayıcısını ve
  `.env` dosyasını otomatik kullanır.
