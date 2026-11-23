"""Hugging Face Space'te calisan chatbot'a baglanan istemci.

Adres, token, endpoint, zaman asimi ve yeniden deneme ayarlari .env'den
okunur (hardcoding yok): HF_CHATBOT_URL, HF_TOKEN, CHATBOT_API_ENDPOINT,
CHATBOT_TIMEOUT, CHATBOT_MAX_RETRIES, CHATBOT_RETRY_BACKOFF.

Uyuyan (sleeping) Space ilk isteklerde gec cevap verebilir veya hata
dondurebilir; bu yuzden baglanti ve her soru ustel bekleme ile yeniden denenir.
"""

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from gradio_client import Client

from kerimbalci_com.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ChatbotError(RuntimeError):
    """Chatbot'a tum denemelere ragmen ulasilamadi veya cevap alinamadi."""


class ChatbotClient:
    """Gradio tabanli chatbot Space'ine soru gonderip cevap alir."""

    def __init__(
        self,
        settings: Settings | None = None,
        client_factory: Callable[..., Any] = Client,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._settings = settings or get_settings()
        self._sleep = sleep
        if not self._settings.hf_chatbot_url:
            raise ValueError("HF_CHATBOT_URL tanimli degil (.env dosyasina ekleyin)")
        self._client = self._with_retry(
            "baglanti",
            lambda: client_factory(
                self._settings.hf_chatbot_url,
                token=self._settings.hf_token or None,
                verbose=False,
                httpx_kwargs={"timeout": self._settings.chatbot_timeout},
                analytics_enabled=False,
            ),
        )

    def _with_retry(self, label: str, operation: Callable[[], T]) -> T:
        """operation'i hata durumunda CHATBOT_MAX_RETRIES kez ustel beklemeyle tekrarlar."""
        attempts = 1 + max(0, self._settings.chatbot_max_retries)
        for attempt in range(1, attempts + 1):
            try:
                return operation()
            except Exception as exc:  # noqa: BLE001 — her hata yeniden denenir
                if attempt == attempts:
                    raise ChatbotError(
                        f"Chatbot {label} {attempts} denemede basarisiz: {type(exc).__name__}: {exc}"
                    ) from exc
                delay = self._settings.chatbot_retry_backoff * 2 ** (attempt - 1)
                logger.warning("Chatbot %s hatasi (%d/%d): %s — %.1fs sonra tekrar",
                               label, attempt, attempts, exc, delay)
                self._sleep(delay)
        raise AssertionError("erisilemez")  # pragma: no cover

    def _ask_once(self, message: str) -> str:
        job = self._client.submit(mesaj=message, api_name=self._settings.chatbot_endpoint)
        try:
            result = job.result(timeout=self._settings.chatbot_timeout)
        except Exception:
            cancel = getattr(job, "cancel", None)
            if callable(cancel):
                cancel()
            raise
        return result if isinstance(result, str) else str(result)

    def ask(self, message: str) -> str:
        """Chatbot'a tek bir mesaj gonderir ve metin cevabini dondurur.

        Zaman asimi veya hata olursa yeniden dener; hepsi basarisizsa ChatbotError.
        """
        logger.debug("Chatbot'a soruluyor: %s", message)
        answer = self._with_retry("sorusu", lambda: self._ask_once(message))
        logger.debug("Chatbot cevabi (%d karakter): %.200s", len(answer), answer)
        return answer
