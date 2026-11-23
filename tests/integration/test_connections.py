"""Dis servislere baglanti testleri (integration).

Bu testler gercek ag baglantisi gerektirir ve .env dosyasindaki
degiskenleri kullanir. Ilgili degisken tanimli degilse test atlanir (skip).

Calistirma:
    uv run pytest -m integration          # sadece baglanti testleri
    uv run pytest -m "not integration"    # baglanti testleri haric
"""

import json
import os
import urllib.request

import pytest

from kerimbalci_com.config import get_settings  # import .env'i yukler

TIMEOUT = get_settings().http_timeout

pytestmark = pytest.mark.integration


def _require_env(key: str) -> str:
    """Degiskeni dondurur; tanimli degilse testi atlar."""
    value = os.getenv(key)
    if not value:
        pytest.skip(f"{key} tanimli degil (.env dosyasina ekleyin)")
    return value


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status, response.read()


def test_hf_chatbot_space_erisebilir():
    """Hugging Face Space'teki chatbot ayakta mi?"""
    url = _require_env("HF_CHATBOT_URL")
    status, _ = _get(url)
    assert status == 200


def test_hf_token_gecerli():
    """HF_TOKEN ile kimlik dogrulama calisiyor mu?"""
    token = _require_env("HF_TOKEN")
    status, body = _get(
        "https://huggingface.co/api/whoami-v2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status == 200
    data = json.loads(body)
    assert "name" in data, "whoami cevabinda kullanici adi yok"


def test_anthropic_api_anahtari_gecerli():
    """ANTHROPIC_API_KEY ile Anthropic API'ye erisilebiliyor mu?"""
    api_key = _require_env("ANTHROPIC_API_KEY")
    status, body = _get(
        "https://api.anthropic.com/v1/models?limit=1",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    assert status == 200
    data = json.loads(body)
    assert data.get("data"), "model listesi bos dondu"


def test_judge_model_erisilebilir():
    """JUDGE_MODEL olarak secilen model API'de mevcut mu?"""
    api_key = _require_env("ANTHROPIC_API_KEY")
    judge_model = _require_env("JUDGE_MODEL")
    status, body = _get(
        f"https://api.anthropic.com/v1/models/{judge_model}",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    assert status == 200
    data = json.loads(body)
    assert data.get("id") == judge_model
