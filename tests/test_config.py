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
