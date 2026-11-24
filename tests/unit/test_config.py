"""config modulunun testleri."""

from kerimbalci_com.config import Settings, _env_bool, get_settings


def test_default_settings(monkeypatch):
    """Hicbir ortam degiskeni yokken mantikli varsayilanlar doner."""
    for key in ("APP_NAME", "ENVIRONMENT", "DEBUG", "LOG_LEVEL"):
        monkeypatch.delenv(key, raising=False)
    settings = get_settings()
    assert settings.app_name == "kerimbalci-com"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.is_production is False


def test_settings_from_env(monkeypatch):
    """Ayarlar ortam degiskenlerinden dinamik olarak okunur."""
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "warning")
    settings = get_settings()
    assert settings.app_name == "test-app"
    assert settings.environment == "production"
    assert settings.debug is True
    assert settings.log_level == "WARNING"
    assert settings.is_production is True


def test_env_bool_variants(monkeypatch):
    """Bool cevirici farkli yazimlari dogru anlar."""
    truthy = ["1", "true", "True", "YES", "on"]
    falsy = ["0", "false", "no", "off", ""]
    for value in truthy:
        monkeypatch.setenv("FLAG", value)
        assert _env_bool("FLAG") is True, value
    for value in falsy:
        monkeypatch.setenv("FLAG", value)
        assert _env_bool("FLAG") is False, value


def test_env_bool_default(monkeypatch):
    """Degisken tanimli degilse verilen varsayilan doner."""
    monkeypatch.delenv("MISSING_FLAG", raising=False)
    assert _env_bool("MISSING_FLAG") is False
    assert _env_bool("MISSING_FLAG", default=True) is True


def test_settings_frozen():
    """Settings nesnesi degistirilemez (immutable) olmali."""
    settings = Settings()
    try:
        settings.debug = True  # type: ignore[misc]
        raised = False
    except AttributeError:
        raised = True
    assert raised


def test_factuality_ayarlari(monkeypatch):
    """Hakem seviyesi varsayilan 3; esik tanimsiz/bos ise None (YAML'daki kullanilir)."""
    monkeypatch.delenv("FACTUALITY_JUDGE_LEVEL", raising=False)
    monkeypatch.delenv("EVAL_FACTUALITY_THRESHOLD", raising=False)
    settings = get_settings()
    assert settings.factuality_judge_level == 3
    assert settings.factuality_threshold is None

    monkeypatch.setenv("FACTUALITY_JUDGE_LEVEL", "1")
    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "")
    settings = get_settings()
    assert settings.factuality_judge_level == 1
    assert settings.factuality_threshold is None

    monkeypatch.setenv("EVAL_FACTUALITY_THRESHOLD", "0.8")
    assert get_settings().factuality_threshold == 0.8


def test_hallucination_ayarlari(monkeypatch):
    """Hakem seviyesi varsayilan 3; esik bos ise None (YAML'daki kullanilir)."""
    monkeypatch.delenv("HALLUCINATION_JUDGE_LEVEL", raising=False)
    monkeypatch.setenv("EVAL_HALLUCINATION_THRESHOLD", "")
    settings = get_settings()
    assert settings.hallucination_judge_level == 3
    assert settings.hallucination_threshold is None

    monkeypatch.setenv("HALLUCINATION_JUDGE_LEVEL", "1")
    monkeypatch.setenv("EVAL_HALLUCINATION_THRESHOLD", "0.7")
    settings = get_settings()
    assert settings.hallucination_judge_level == 1
    assert settings.hallucination_threshold == 0.7


def test_eval_runner_ayarlari(monkeypatch):
    """Eszamanlilik, tag listesi ve rapor klasoru ortamdan okunur."""
    for key in ("EVAL_CONCURRENCY", "EVAL_TAGS", "EVAL_REPORT_DIR"):
        monkeypatch.delenv(key, raising=False)
    settings = get_settings()
    assert settings.eval_concurrency == 4
    assert settings.eval_tags == ()
    assert settings.eval_report_dir.name == "reports"

    monkeypatch.setenv("EVAL_CONCURRENCY", "8")
    monkeypatch.setenv("EVAL_TAGS", " false_premise , ,unanswerable")
    monkeypatch.setenv("EVAL_REPORT_DIR", "out/raporlar")
    settings = get_settings()
    assert settings.eval_concurrency == 8
    assert settings.eval_tags == ("false_premise", "unanswerable")
    assert settings.eval_report_dir.parts[-2:] == ("out", "raporlar")


def test_http_ve_site_ayarlari(monkeypatch):
    """Zaman asimi, site adresi ve calisma klasoru ortamdan okunur."""
    for key in ("HTTP_TIMEOUT", "SITE_URL", "SITE_WORKDIR"):
        monkeypatch.delenv(key, raising=False)
    settings = get_settings()
    assert settings.http_timeout == 30
    assert settings.site_url == "https://kerimbalci.com"
    assert settings.site_workdir.parts[-2:] == (".cache", "site")

    monkeypatch.setenv("HTTP_TIMEOUT", "5")
    monkeypatch.setenv("SITE_URL", "https://ornek.com")
    monkeypatch.setenv("SITE_WORKDIR", "tmp/x")
    settings = get_settings()
    assert (settings.http_timeout, settings.site_url) == (5, "https://ornek.com")
    assert settings.site_workdir.parts[-2:] == ("tmp", "x")


def test_chatbot_ve_kalite_kapisi_ayarlari(monkeypatch):
    """Chatbot zaman asimi/yeniden deneme ve kalite kapisi esigi ortamdan okunur."""
    for key in ("CHATBOT_TIMEOUT", "CHATBOT_MAX_RETRIES", "CHATBOT_RETRY_BACKOFF", "EVAL_MIN_PASS_RATE"):
        monkeypatch.delenv(key, raising=False)
    s = get_settings()
    assert (s.chatbot_timeout, s.chatbot_max_retries, s.chatbot_retry_backoff) == (60.0, 2, 2.0)
    assert s.eval_min_pass_rate == 0.85

    monkeypatch.setenv("CHATBOT_TIMEOUT", "10")
    monkeypatch.setenv("CHATBOT_MAX_RETRIES", "0")
    monkeypatch.setenv("CHATBOT_RETRY_BACKOFF", "0.5")
    monkeypatch.setenv("EVAL_MIN_PASS_RATE", "0.9")
    s = get_settings()
    assert (s.chatbot_timeout, s.chatbot_max_retries, s.chatbot_retry_backoff) == (10.0, 0, 0.5)
    assert s.eval_min_pass_rate == 0.9


def test_compare_esigi(monkeypatch):
    monkeypatch.delenv("EVAL_COMPARE_MIN_DELTA", raising=False)
    assert get_settings().eval_compare_min_delta == 0.2
    monkeypatch.setenv("EVAL_COMPARE_MIN_DELTA", "0.1")
    assert get_settings().eval_compare_min_delta == 0.1


def test_expected_behavior_ayari(monkeypatch):
    monkeypatch.delenv("EVAL_EXPECTED_BEHAVIOR", raising=False)
    assert get_settings().eval_expected_behavior is True
    monkeypatch.setenv("EVAL_EXPECTED_BEHAVIOR", "false")
    assert get_settings().eval_expected_behavior is False
