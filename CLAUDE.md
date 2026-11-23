# Proje Talimatları

Bu dosya projenin çalışma kurallarını tanımlar. Projeye katkı yapan herkes
(insan veya AI) bu kurallara uyar. Claude Code bu dosyayı her oturumun
başında otomatik olarak okur.

Proje: kerimbalci.com chatbot'u için LLM eval otomasyon framework'ü
(deepeval + Confident AI). Ayrıntılı dokümantasyon **`instructions/`**
klasöründedir (içindekiler: `instructions/README.md`); bir konuda çalışmadan
önce ilgili dosyayı oku.

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
- Değişkenlerin tam listesi ve açıklamaları: `instructions/configuration.md`.
  Yeni değişken eklendiğinde o tablo da güncellenir.
- Gizli anahtarlar (`HF_TOKEN`, `ANTHROPIC_API_KEY`, `CONFIDENT_API_KEY`)
  loglanmaz, koda veya dokümana yazılmaz.

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

- Her yeni modül/işlev için `tests/` altına test yazılır:
  - `tests/unit/` — ağ/API gerektirmeyen testler (sahte chatbot/hakem),
  - `tests/integration/` — dış servis bağlantı testleri (`-m integration`),
  - `tests/<suite>/` — LLM eval testleri (`-m eval`, **ücretli**).
- Ortak fixture'lar `tests/conftest.py`'dedir; ayar eksikse test atlanır (skip).
- Eval testleri izin alınmadan tam set olarak çalıştırılmaz; önce `-k` ile
  küçük bir alt kümede denenir.
- Testlerde ortam değişkenleri `monkeypatch` ile ayarlanır; gerçek `.env`
  dosyasına bağımlı test yazılmaz.
- Hızlı kontrol: `uv run pytest -m "not integration"`
  (ayarlar `pyproject.toml` → `[tool.pytest.ini_options]` bölümünde).

## 6. Git

- Depo `uv init` ile oluşturuldu; gizli ve üretilen dosyalar `.gitignore`'dadır.
- `.env`, `.venv`, `__pycache__`, `.pytest_cache`, `.deepeval/`, `.cache/`,
  `reports/` asla commit edilmez.
- Anlamlı, küçük commit'ler atılır; commit mesajı değişikliği özetler.

## 7. Bağımlılık Ekleme

- Çalışma zamanı bağımlılığı: `uv add <paket>`
- Geliştirme bağımlılığı (test, lint vb.): `uv add --dev <paket>`
- `uv.lock` dosyası commit edilir; böylece ortam her makinede aynı kurulur.

## 8. Veri, Hakem ve Eval Yapısı

- **Veri ve kriter koddan ayrıdır:** sorular `dataset/<suite>/*.json`,
  hakem tanımları `judges/<suite>_judge/*.yaml`. Soru veya kriter değiştirmek
  için Python kodu değiştirilmez.
- Dataset beklenen cevapları yalnızca site içeriğine dayanır; her kayıt
  birebir `evidence` alıntısı taşır (`instructions/dataset.md`).
- Eval kodu `src/kerimbalci_com/evals/` altındadır: `EvalSuite` (suite tanımı),
  `suite_runner` (paralel çalıştırma), `judge_config` (YAML → GEval),
  `reporter`, `suites/<ad>_suite.py`. Yeni suite = yeni `suites/<ad>_suite.py`
  + `SUITES` kaydı + `dataset/<ad>/` + `judges/<ad>_judge/` + `tests/<ad>/`.
