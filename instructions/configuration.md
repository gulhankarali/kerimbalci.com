# Dinamik Yapılandırma (Hardcoding Yasağı)

Kodda hiçbir ayar, yol, URL, anahtar veya eşik değeri sabit yazılmaz. Akış:

```
.env  →  python-dotenv (config.py yüklerken)  →  Settings  →  get_settings()
```

`src/kerimbalci_com/config.py`, proje kökünü `Path(__file__)` ile bulur ve
`.env`'i oradan yükler. `get_settings()` her çağrıldığında **güncel ortamdan**
yeni bir `Settings` üretir (testlerde `monkeypatch` bu sayede çalışır).
Öncelik: **sistem ortam değişkeni > `.env` > koddaki varsayılan**.

## Değişkenler

| Değişken | Okuyan | Açıklama |
|---|---|---|
| `APP_NAME` | `Settings.app_name` | Uygulama / logger adı |
| `ENVIRONMENT` | `Settings.environment` | `development` \| `staging` \| `production` |
| `DEBUG` | `Settings.debug` | `true` ise log seviyesi otomatik DEBUG |
| `LOG_LEVEL` | `Settings.log_level` | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `JUDGE_MODEL` | `Settings.judge_model` | Hakem olarak kullanılacak Anthropic modeli |
| `HF_CHATBOT_URL` | `Settings.hf_chatbot_url` | Test edilen chatbot'un HF Space adresi |
| `CHATBOT_API_ENDPOINT` | `Settings.chatbot_endpoint` | Gradio endpoint (varsayılan `/cevapla`) |
| `HF_TOKEN` | `Settings.hf_token` | Hugging Face token (gizli) |
| `FACTUALITY_JUDGE_LEVEL` | `Settings.factuality_judge_level` | Hakem seviyesi: 1 basic, 2 intermediate, 3 advanced (vars. 3) |
| `EVAL_FACTUALITY_THRESHOLD` | `Settings.factuality_threshold` | Eşik (0-1); boşsa hakem YAML'ındaki `threshold` |
| `EVAL_CONCURRENCY` | `Settings.eval_concurrency` | Runner'da aynı anda çalışan case sayısı (vars. 4) |
| `EVAL_TAGS` | `Settings.eval_tags` | Runner'da yalnızca bu tag'ler (virgülle; boş = hepsi) |
| `EVAL_REPORT_DIR` | `Settings.eval_report_dir` | JSON raporların klasörü, proje köküne göre (vars. `reports`) |
| `ANTHROPIC_API_KEY` | Anthropic SDK / deepeval | Hakem model API anahtarı (gizli) |
| `CONFIDENT_API_KEY` | deepeval | Sonuçları Confident AI'ya gönderir (gizli, opsiyonel) |
| `HTTP_TIMEOUT` | `Settings.http_timeout` | Dış HTTP istekleri zaman aşımı, sn (vars. 30) |
| `SITE_URL` | `Settings.site_url` | Dataset için taranacak site (vars. `https://kerimbalci.com`) |
| `SITE_WORKDIR` | `Settings.site_workdir` | İndirilen sayfa metinleri, proje köküne göre (vars. `.cache/site`, git'e girmez) |
| `CRAWL_USER_AGENT` | `Settings.crawl_user_agent` | Tarama isteklerinin User-Agent başlığı |

## Yeni ayar eklemek

1. `.env.example`'a açıklama satırıyla birlikte ekle (gizli değer yazma).
2. Kendi `.env` dosyana gerçek değeri yaz.
3. `Settings`'e alan ekle:
   `yeni_ayar: str = field(default_factory=lambda: os.getenv("YENI_AYAR", "varsayilan"))`
4. Kodda `get_settings().yeni_ayar` ile kullan.
5. `tests/unit/test_config.py`'ye varsayılan + ortamdan okuma testi ekle.
6. Bu tabloya ekle.

## Gizli bilgiler

- `.env` asla commit edilmez (`.gitignore`'da). `.env.example` commit edilir
  ve yalnızca örnek değer içerir.
- Gizli değerler loglanmaz.
