"""Timeout and retry behaviour of ChatbotClient (fake Gradio client)."""

from concurrent.futures import TimeoutError as FutureTimeout

import pytest

from kerimbalci_com.chatbot import ChatbotClient, ChatbotError
from kerimbalci_com.config import get_settings


class FakeJob:
    def __init__(self, outcome):
        self.outcome = outcome
        self.cancelled = False
        self.timeout = None

    def result(self, timeout=None):
        self.timeout = timeout
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    def cancel(self):
        self.cancelled = True


class FakeGradio:
    """submit() returns the next outcome on each call (raised if it is an Exception)."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.jobs: list[FakeJob] = []
        self.calls: list[dict] = []

    def submit(self, **kwargs):
        self.calls.append(kwargs)
        job = FakeJob(self.outcomes.pop(0))
        self.jobs.append(job)
        return job


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("HF_CHATBOT_URL", "https://example.hf.space")
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.setenv("CHATBOT_API_ENDPOINT", "/cevapla")
    monkeypatch.setenv("CHATBOT_TIMEOUT", "5")
    monkeypatch.setenv("CHATBOT_MAX_RETRIES", "2")
    monkeypatch.setenv("CHATBOT_RETRY_BACKOFF", "1")


def make_client(gradio, factory_errors=0):
    sleeps: list[float] = []
    state = {"errors": factory_errors, "kwargs": None}

    def factory(url, **kwargs):
        state["kwargs"] = {"url": url, **kwargs}
        if state["errors"]:
            state["errors"] -= 1
            raise ConnectionError("space is sleeping")
        return gradio

    client = ChatbotClient(get_settings(), client_factory=factory, sleep=sleeps.append)
    return client, sleeps, state


def test_successful_answer_and_settings(env):
    gradio = FakeGradio(["Merhaba"])
    client, sleeps, state = make_client(gradio)

    assert client.ask("Selam") == "Merhaba"
    assert gradio.calls == [{"mesaj": "Selam", "api_name": "/cevapla"}]
    assert gradio.jobs[0].timeout == 5.0
    assert state["kwargs"]["httpx_kwargs"] == {"timeout": 5.0}
    assert state["kwargs"]["token"] is None and state["kwargs"]["analytics_enabled"] is False
    assert sleeps == []


def test_timeout_cancels_and_retries_with_exponential_backoff(env):
    gradio = FakeGradio([FutureTimeout(), RuntimeError("502"), 42])
    client, sleeps, _ = make_client(gradio)

    assert client.ask("Question") == "42"  # a non-text answer is converted to str
    assert sleeps == [1.0, 2.0]
    assert gradio.jobs[0].cancelled and gradio.jobs[1].cancelled


def test_chatbot_error_when_all_attempts_fail(env):
    gradio = FakeGradio([RuntimeError("a"), RuntimeError("b"), RuntimeError("c")])
    client, sleeps, _ = make_client(gradio)

    with pytest.raises(ChatbotError, match="failed after 3 attempts: RuntimeError: c"):
        client.ask("Question")
    assert len(gradio.calls) == 3 and sleeps == [1.0, 2.0]


def test_connection_is_retried_too(env):
    client, sleeps, _ = make_client(FakeGradio(["ok"]), factory_errors=1)
    assert client.ask("x") == "ok"
    assert sleeps == [1.0]


def test_retries_disabled(env, monkeypatch):
    monkeypatch.setenv("CHATBOT_MAX_RETRIES", "0")
    gradio = FakeGradio([RuntimeError("a")])
    client, sleeps, _ = make_client(gradio)
    with pytest.raises(ChatbotError, match="after 1 attempts"):
        client.ask("x")
    assert sleeps == []


def test_error_without_url(monkeypatch):
    monkeypatch.setenv("HF_CHATBOT_URL", "")
    with pytest.raises(ValueError, match="HF_CHATBOT_URL"):
        ChatbotClient(get_settings(), client_factory=lambda *a, **k: None)
