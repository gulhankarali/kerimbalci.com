"""Tum testlerde ortak fixture'lar.

Gercek servis gerektiren fixture'lar ilgili ayar .env'de yoksa testi atlar
(skip); boylece eksik ayar testi basarisiz yapmaz.

Klasorler:
    tests/unit/         ag/API gerektirmeyen birim testler
    tests/integration/  dis servis baglanti testleri      (-m integration)
    tests/<suite>/      suite bazli LLM eval testleri      (-m eval, ucretli)
"""

import pytest
from deepeval.models import AnthropicModel

from kerimbalci_com.chatbot import ChatbotClient
from kerimbalci_com.config import Settings, get_settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def chatbot(settings: Settings) -> ChatbotClient:
    """HF Space'teki gercek chatbot istemcisi."""
    if not settings.hf_chatbot_url:
        pytest.skip("HF_CHATBOT_URL tanimli degil (.env dosyasina ekleyin)")
    return ChatbotClient(settings)


@pytest.fixture(scope="session")
def judge_model(settings: Settings) -> AnthropicModel:
    """Hakem (LLM-as-judge) modeli."""
    if not settings.judge_model:
        pytest.skip("JUDGE_MODEL tanimli degil (.env dosyasina ekleyin)")
    return AnthropicModel(model=settings.judge_model)
