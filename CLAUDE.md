# Proje Talimatları (INSTRUCTIONS)

Bu dosya projenin çalışma kurallarını tanımlar. Projeye katkı yapan herkes
(insan veya AI) bu kurallara uyar.

## 1. Araç Zinciri

- Paket/proje yönetimi **yalnızca `uv`** ile yapılır. `pip install`,
  `python -m venv` gibi komutlar kullanılmaz.
- Python sürümü `.python-version` dosyasında tanımlıdır (3.11).
- Testler **pytest** ile yazılır ve `uv run pytest` ile çalıştırılır.

## 2. Dinamiklik — Hardcoding Yasağı

- **Hiçbir ayar, yol, URL, anahtar veya sabit değer koda gömülmez.**
- Tüm yapılandırma ortam değişkenlerinden okunur:
  `.env` → `python-dotenv` → `src/kerimbalci_com/config.py` → `Settings`.
- Yeni bir ayar gerektiğinde sıra şöyledir:
  1. `.env.example` dosyasına açıklamalı satır ekle (varsayılan/örnek değerle),
  2. Kendi `.env` dosyana gerçek değeri yaz,
  3. `config.py` içindeki `Settings` sınıfına alanı ekle,
  4. Kodda `get_settings()` üzerinden kullan.
- Dosya yolları `Path(__file__)` tabanlı dinamik hesaplanır; mutlak yol yazılmaz.

## 3. Ortam Değişkenleri (.env)

- `.env` gerçek değerleri tutar, **asla git'e commit edilmez** (`.gitignore`'da).
- `.env.example` şablondur, gizli bilgi içermez ve commit edilir.
- Yeni kurulum: `cp .env.example .env`
- Mevcut değişkenler: `APP_NAME`, `ENVIRONMENT`, `DEBUG`, `LOG_LEVEL`.

## 4. Debug

- `.env` içinde `DEBUG=true` yapıldığında log seviyesi otomatik `DEBUG` olur
  ve ayrıntılı loglar görünür (`config.setup_logging`).
- VS Code'da **F5** ile debug: `.vscode/launch.json` üç yapılandırma içerir:
  - *Uygulamayı Debug Et* — paketi `python -m` ile başlatır,
  - *Açık Dosyayı Debug Et* — editörde açık dosyayı çalıştırır,
  - *Testleri Debug Et* — pytest'i debugger altında çalıştırır.
- Tüm debug yapılandırmaları `.env` dosyasını otomatik yükler.
- `print()` ile debug yapılmaz; `logging` kullanılır.

## 5. Test

- Her yeni modül/işlev için `tests/` altına test yazılır.
- Testlerde ortam değişkenleri `monkeypatch` ile ayarlanır; gerçek `.env`
  dosyasına bağımlı test yazılmaz.
- Çalıştırma: `uv run pytest` (ayarlar `pyproject.toml` →
  `[tool.pytest.ini_options]` bölümünde).

## 6. Git

- Depo `uv init` ile oluşturuldu; gizli ve üretilen dosyalar `.gitignore`'dadır.
- `.env`, `.venv`, `__pycache__`, `.pytest_cache` asla commit edilmez.
- Anlamlı, küçük commit'ler atılır; commit mesajı değişikliği özetler.

## 7. Bağımlılık Ekleme

- Çalışma zamanı bağımlılığı: `uv add <paket>`
- Geliştirme bağımlılığı (test, lint vb.): `uv add --dev <paket>`
- `uv.lock` dosyası commit edilir; böylece ortam her makinede aynı kurulur.
