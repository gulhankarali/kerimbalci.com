"""Client for the chatbot running on a Hugging Face Space.

URL, token, endpoint, timeout and retry settings are read from .env (no
hardcoding): HF_CHATBOT_URL, HF_TOKEN, CHATBOT_API_ENDPOINT, CHATBOT_TIMEOUT,
CHATBOT_MAX_RETRIES, CHATBOT_RETRY_BACKOFF.

A sleeping Space may answer slowly or fail on the first requests, so the
connection and every question are retried with exponential backoff.
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
    """The chatbot could not be reached or did not answer after all retries."""


class ChatbotClient:
    """Sends questions to the Gradio-based chatbot Space and returns the answers."""

    def __init__(
        self,
        settings: Settings | None = None,
        client_factory: Callable[..., Any] = Client,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._settings = settings or get_settings()
        self._sleep = sleep
        if not self._settings.hf_chatbot_url:
            raise ValueError("HF_CHATBOT_URL is not set (add it to the .env file)")
        self._client = self._with_retry(
            "connection",
            lambda: client_factory(
                self._settings.hf_chatbot_url,
                token=self._settings.hf_token or None,
                verbose=False,
                httpx_kwargs={"timeout": self._settings.chatbot_timeout},
                analytics_enabled=False,
            ),
        )

    def _with_retry(self, label: str, operation: Callable[[], T]) -> T:
        """Retries `operation` up to CHATBOT_MAX_RETRIES times with exponential backoff."""
        attempts = 1 + max(0, self._settings.chatbot_max_retries)
        for attempt in range(1, attempts + 1):
            try:
                return operation()
            except Exception as exc:  # noqa: BLE001 — every error is retried
                if attempt == attempts:
                    raise ChatbotError(
                        f"Chatbot {label} failed after {attempts} attempts: {type(exc).__name__}: {exc}"
                    ) from exc
                delay = self._settings.chatbot_retry_backoff * 2 ** (attempt - 1)
                logger.warning("Chatbot %s error (%d/%d): %s — retrying in %.1fs",
                               label, attempt, attempts, exc, delay)
                self._sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover

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
        """Sends one message to the chatbot and returns its text answer.

        Retries on timeout or error; raises ChatbotError if every attempt fails.
        """
        logger.debug("Asking the chatbot: %s", message)
        answer = self._with_retry("question", lambda: self._ask_once(message))
        logger.debug("Chatbot answer (%d characters): %.200s", len(answer), answer)
        return answer
