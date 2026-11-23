"""ChatbotClient'in zaman asimi ve yeniden deneme davranisi (sahte Gradio istemcisi)."""

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
    """submit() her cagrida sirayla bir sonuc dondurur (Exception ise firlatilir)."""

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
    monkeypatch.setenv("HF_CHATBOT_URL", "https://ornek.hf.space")
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
            raise ConnectionError("space uyuyor")
        return gradio

    client = ChatbotClient(get_settings(), client_factory=factory, sleep=sleeps.append)
    return client, sleeps, state


def test_basarili_cevap_ve_ayarlar(env):
    gradio = FakeGradio(["Merhaba"])
    client, sleeps, state = make_client(gradio)

    assert client.ask("Selam") == "Merhaba"
    assert gradio.calls == [{"mesaj": "Selam", "api_name": "/cevapla"}]
    assert gradio.jobs[0].timeout == 5.0
    assert state["kwargs"]["httpx_kwargs"] == {"timeout": 5.0}
    assert state["kwargs"]["token"] is None and state["kwargs"]["analytics_enabled"] is False
    assert sleeps == []


def test_zaman_asiminda_iptal_edip_ustel_beklemeyle_tekrar_dener(env):
    gradio = FakeGradio([FutureTimeout(), RuntimeError("502"), 42])
    client, sleeps, _ = make_client(gradio)

    assert client.ask("Soru") == "42"  # metin olmayan cevap str'e cevrilir
    assert sleeps == [1.0, 2.0]
    assert gradio.jobs[0].cancelled and gradio.jobs[1].cancelled


def test_tum_denemeler_basarisizsa_chatbot_error(env):
    gradio = FakeGradio([RuntimeError("a"), RuntimeError("b"), RuntimeError("c")])
    client, sleeps, _ = make_client(gradio)

    with pytest.raises(ChatbotError, match="3 denemede basarisiz: RuntimeError: c"):
        client.ask("Soru")
    assert len(gradio.calls) == 3 and sleeps == [1.0, 2.0]


def test_baglanti_da_yeniden_denenir(env):
    client, sleeps, _ = make_client(FakeGradio(["ok"]), factory_errors=1)
    assert client.ask("x") == "ok"
    assert sleeps == [1.0]


def test_yeniden_deneme_kapali(env, monkeypatch):
    monkeypatch.setenv("CHATBOT_MAX_RETRIES", "0")
    gradio = FakeGradio([RuntimeError("a")])
    client, sleeps, _ = make_client(gradio)
    with pytest.raises(ChatbotError, match="1 denemede"):
        client.ask("x")
    assert sleeps == []


def test_url_yoksa_hata(monkeypatch):
    monkeypatch.setenv("HF_CHATBOT_URL", "")
    with pytest.raises(ValueError, match="HF_CHATBOT_URL"):
        ChatbotClient(get_settings(), client_factory=lambda *a, **k: None)
