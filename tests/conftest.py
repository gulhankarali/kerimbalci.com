"""Fixtures shared by all tests.

Fixtures that need a real service skip the test when the related setting is
missing from .env, so a missing setting does not fail the test.

Folders:
    tests/unit/         unit tests without network/API
    tests/integration/  external service connection tests   (-m integration)
    tests/<suite>/      per-suite LLM eval tests             (-m eval, paid)
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
    """Real chatbot client for the HF Space."""
    if not settings.hf_chatbot_url:
        pytest.skip("HF_CHATBOT_URL is not set (add it to the .env file)")
    return ChatbotClient(settings)


@pytest.fixture(scope="session")
def judge_model(settings: Settings) -> AnthropicModel:
    """Judge (LLM-as-judge) model."""
    if not settings.judge_model:
        pytest.skip("JUDGE_MODEL is not set (add it to the .env file)")
    return AnthropicModel(model=settings.judge_model)
