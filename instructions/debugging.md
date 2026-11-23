# Debug

## Loglama
- `print()` kullanılmaz; her modülde `logger = logging.getLogger(__name__)`.
- `.env` → `DEBUG=true` olunca `setup_logging()` seviyeyi otomatik DEBUG
  yapar; aksi halde `LOG_LEVEL` kullanılır.
- pytest canlı log açıktır (`log_cli = true`, INFO). Ayrıntı için:
  `uv run pytest --log-cli-level=DEBUG ...`
- `ChatbotClient.ask` DEBUG seviyesinde soruyu ve cevabın ilk 200
  karakterini loglar — eval'de chatbot'un ne döndürdüğünü görmek için
  kullanışlıdır.

## VS Code (F5)

`.vscode/launch.json` üç yapılandırma içerir; hepsi `.env`'i yükler:

| Yapılandırma | Ne yapar |
|---|---|
| Python: Uygulamayı Debug Et | `python -m kerimbalci_com` |
| Python: Açık Dosyayı Debug Et | Editörde açık dosyayı çalıştırır |
| Pytest: Testleri Debug Et | pytest'i debugger altında çalıştırır (`justMyCode: false`) |

Tek bir eval kaydını debug etmek için Pytest yapılandırmasının `args`
alanına geçici olarak `["-v", "tests/factuality/", "-k", "fact-001"]`
yazılabilir (commit etmeyin).

## Sık karşılaşılanlar

| Belirti | Olası neden |
|---|---|
| Testler `SKIPPED` | İlgili değişken `.env`'de yok (`HF_CHATBOT_URL`, `JUDGE_MODEL` …) |
| `DatasetError` | Dataset JSON'unda eksik alan / tekrarlı id — mesaj kaydı gösterir |
| `JudgeConfigError` | Hakem YAML'ı şemaya uymuyor (eksik alan, rubric boşluğu/çakışması) — mesaj dosyayı gösterir |
| Chatbot boş cevap | Space uyuyor olabilir; `test_hf_chatbot_space_erisebilir` ile kontrol edin |
| Hakem 401/404 | `ANTHROPIC_API_KEY` veya `JUDGE_MODEL` hatalı — `test_connections.py` |
