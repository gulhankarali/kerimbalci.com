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
| `CHATBOT_TIMEOUT` | `Settings.chatbot_timeout` | Tek soru için zaman aşımı, sn (vars. 60) |
| `CHATBOT_MAX_RETRIES` | `Settings.chatbot_max_retries` | Hata/zaman aşımında yeniden deneme sayısı (vars. 2; 0 = kapalı) |
| `CHATBOT_RETRY_BACKOFF` | `Settings.chatbot_retry_backoff` | İlk bekleme, sn; her denemede iki katı (vars. 2 → 2, 4, …) |
| `FACTUALITY_JUDGE_LEVEL` | `Settings.factuality_judge_level` | Hakem seviyesi: 1 basic, 2 intermediate, 3 advanced (vars. 3) |
| `EVAL_FACTUALITY_THRESHOLD` | `Settings.factuality_threshold` | Eşik (0-1); boşsa hakem YAML'ındaki `threshold` |
| `HALLUCINATION_JUDGE_LEVEL` | `Settings.hallucination_judge_level` | Hallucination hakem seviyesi: 1 basic, 2 intermediate, 3 advanced (vars. 3) |
| `EVAL_HALLUCINATION_THRESHOLD` | `Settings.hallucination_threshold` | Hallucination eşiği (0-1); boşsa hakem YAML'ındaki `threshold` |
| `EVAL_EXPECTED_BEHAVIOR` | `Settings.eval_expected_behavior` | Factuality ve hallucination suite'lerinde ikinci metric (davranış); `false` = kapalı (vars. `true`) |
| `EVAL_CONCURRENCY` | `Settings.eval_concurrency` | Runner'da aynı anda çalışan case sayısı (vars. 4) |
| `EVAL_TAGS` | `Settings.eval_tags` | Runner'da yalnızca bu tag'ler (virgülle; boş = hepsi) |
| `EVAL_MIN_PASS_RATE` | `Settings.eval_min_pass_rate` | Runner kalite kapısı: geçen case oranı alt sınırı (vars. 0.85) |
| `EVAL_COMPARE_MIN_DELTA` | `Settings.eval_compare_min_delta` | Rapor karşılaştırmada "puanı değişen" eşiği (vars. 0.2) |
| `EVAL_REPORT_DIR` | `Settings.eval_report_dir` | JSON raporların klasörü, proje köküne göre (vars. `reports`) |
| `ANTHROPIC_API_KEY` | Anthropic SDK / deepeval | Hakem model API anahtarı (gizli) |
| `CONFIDENT_API_KEY` | deepeval | Sonuçları Confident AI'ya gönderir (gizli, opsiyonel) |
| `ANTHROPIC_COST_PER_INPUT_TOKEN` / `..._OUTPUT_TOKEN` | deepeval | Opsiyonel: hakem fiyatı (token başına USD); boşsa deepeval'in tablosu |
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

## GitHub Actions

CI'da `.env` yoktur; değerler ortam değişkeni olarak verilir
(repo → Settings → Secrets and variables → Actions):

| Tür | Ad |
|---|---|
| Secret | `HF_TOKEN`, `ANTHROPIC_API_KEY`, `CONFIDENT_API_KEY` (opsiyonel) |
| Variable | `HF_CHATBOT_URL`, `JUDGE_MODEL`, `CHATBOT_API_ENDPOINT` (opsiyonel) |

Diğer ayarlar koddaki varsayılanlarla çalışır; değiştirmek için
`.github/workflows/eval.yml` → `env:` bölümüne eklenir.

## Gizli bilgiler

- `.env` asla commit edilmez (`.gitignore`'da). `.env.example` commit edilir
  ve yalnızca örnek değer içerir.
- Gizli değerler loglanmaz.
