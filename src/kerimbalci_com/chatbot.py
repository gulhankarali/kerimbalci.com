"""Hugging Face Space'te calisan chatbot'a baglanan istemci.

Adres, token ve endpoint .env'den okunur (hardcoding yok):
HF_CHATBOT_URL, HF_TOKEN, CHATBOT_API_ENDPOINT.
"""

import logging

from gradio_client import Client

from kerimbalci_com.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ChatbotClient:
    """Gradio tabanli chatbot Space'ine soru gonderip cevap alir."""

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        if not self._settings.hf_chatbot_url:
            raise ValueError("HF_CHATBOT_URL tanimli degil (.env dosyasina ekleyin)")
        self._client = Client(
            self._settings.hf_chatbot_url,
            token=self._settings.hf_token or None,
            verbose=False,
        )

    def ask(self, message: str) -> str:
        """Chatbot'a tek bir mesaj gonderir ve metin cevabini dondurur."""
        logger.debug("Chatbot'a soruluyor: %s", message)
        result = self._client.predict(
            mesaj=message,
            api_name=self._settings.chatbot_endpoint,
        )
        answer = result if isinstance(result, str) else str(result)
        logger.debug("Chatbot cevabi (%d karakter): %.200s", len(answer), answer)
        return answer
