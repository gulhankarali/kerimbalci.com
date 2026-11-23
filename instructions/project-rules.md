# Proje Kuralları

Temel kurallar `CLAUDE.md`'dedir; bu dosya onları ayrıntılandırır.
Çelişki olursa `CLAUDE.md` geçerlidir.

## Araçlar
- Paket yönetimi yalnızca `uv`: `uv add <paket>`, `uv add --dev <paket>`,
  `uv run <komut>`. `pip`/`venv` kullanılmaz.
- `deepeval`, `anthropic`, `gradio-client`, `python-dotenv`, `pyyaml` çalışma
  zamanı bağımlılığıdır (`src/kerimbalci_com/evals` kullanır); `pytest` dev grubundadır.

## Kod
- **Hardcoding yok:** ayar, URL, anahtar, eşik, yol → `.env` + `Settings`
  (bkz. `configuration.md`). Yollar `PROJECT_ROOT` / `Path(__file__)` tabanlı.
- **Veri ve prompt koddan ayrı:** sorular `dataset/`, hakem kriterleri
  `judges/` altındaki YAML'larda durur.
- `print()` yok; modül başında `logger = logging.getLogger(__name__)`.
- Python dosyalarında açıklama, log ve hata mesajları ASCII Türkçe
  yazılır (ör. `tanimli degil`); md ve JSON dosyalarında Türkçe karakter
  kullanılır.
- Tip ipuçları kullanılır (`str | None`); fonksiyonlarda kısa docstring.
- Hata durumunda anlamlı mesajla özel exception (ör. `DatasetError`).

## Test
- Her yeni modül/işlev için `tests/` altında test.
- Ortam değişkenleri `monkeypatch` ile; gerçek `.env`'e bağımlı birim test yok.
- Ağ gerektiren test `integration`, ücretli LLM çağrısı yapan test ayrıca
  `eval` marker'ı taşır. Eksik ayar varsa test `skip` eder, fail etmez.

## Dataset
- Beklenen cevaplar yalnızca site içeriğine dayanır, her kayıt `evidence`
  içerir (bkz. `dataset.md`).

## Git
- Bkz. `git.md`. `.env` ve üretilen dosyalar asla commit edilmez.
