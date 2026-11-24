"""Connection tests for external services (integration).

These tests need a real network connection and use the variables from the
.env file. A test is skipped when its variable is not set.

Usage:
    uv run pytest -m integration          # connection tests only
    uv run pytest -m "not integration"    # everything except connection tests
"""

import json
import os
import urllib.request

import pytest

from kerimbalci_com.config import get_settings  # importing loads .env

TIMEOUT = get_settings().http_timeout

pytestmark = pytest.mark.integration


def _require_env(key: str) -> str:
    """Returns the variable; skips the test if it is not set."""
    value = os.getenv(key)
    if not value:
        pytest.skip(f"{key} is not set (add it to the .env file)")
    return value


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status, response.read()


def test_hf_chatbot_space_is_reachable():
    """Is the chatbot on the Hugging Face Space up?"""
    url = _require_env("HF_CHATBOT_URL")
    status, _ = _get(url)
    assert status == 200


def test_hf_token_is_valid():
    """Does authentication with HF_TOKEN work?"""
    token = _require_env("HF_TOKEN")
    status, body = _get(
        "https://huggingface.co/api/whoami-v2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status == 200
    data = json.loads(body)
    assert "name" in data, "no user name in the whoami response"


def test_anthropic_api_key_is_valid():
    """Can the Anthropic API be reached with ANTHROPIC_API_KEY?"""
    api_key = _require_env("ANTHROPIC_API_KEY")
    status, body = _get(
        "https://api.anthropic.com/v1/models?limit=1",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    assert status == 200
    data = json.loads(body)
    assert data.get("data"), "the model list is empty"


def test_judge_model_is_available():
    """Is the model selected as JUDGE_MODEL available in the API?"""
    api_key = _require_env("ANTHROPIC_API_KEY")
    judge_model = _require_env("JUDGE_MODEL")
    status, body = _get(
        f"https://api.anthropic.com/v1/models/{judge_model}",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    assert status == 200
    data = json.loads(body)
    assert data.get("id") == judge_model


def test_chatbot_answers_a_real_question(chatbot):
    """Can ChatbotClient get an answer from the real Space (with timeout/retry)?

    Does not call the judge model; free. Fixture: tests/conftest.py.
    """
    answer = chatbot.ask("Merhaba")
    assert isinstance(answer, str) and answer.strip()
