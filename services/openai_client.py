from __future__ import annotations

import io
import logging
from openai import AsyncOpenAI

LOGGER = logging.getLogger(__name__)


class OpenAIClientError(RuntimeError):
    """Base exception for OpenAI client issues."""


class OpenAIClient:
    """Thin async wrapper around the OpenAI Responses API."""

    def __init__(
        self,
        api_key: str,
        *,
        text_model: str,
        vision_model: str,
        transcribe_model: str,
        temperature: float = 0.6,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._text_model = text_model
        self._vision_model = vision_model
        self._transcribe_model = transcribe_model
        self._temperature = temperature

    async def generate_text(self, prompt: str) -> str:
        """Call GPT-4o text model with a simple user prompt."""

        try:
            response = await self._client.chat.completions.create(
                model=self._text_model,
                temperature=self._temperature,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # pragma: no cover - network failure
            raise OpenAIClientError("Не удалось получить ответ от OpenAI") from exc

        content = response.choices[0].message.content or ""
        LOGGER.debug("Text completion tokens: %s", response.usage)
        return content.strip()

    async def generate_vision(
        self,
        prompt: str,
        image_base64_url: str,
    ) -> str:
        """Call GPT-4o vision model with a text+image payload."""

        payload = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_base64_url}},
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self._vision_model,
                temperature=self._temperature,
                messages=[{"role": "user", "content": payload}],
            )
        except Exception as exc:  # pragma: no cover - network failure
            raise OpenAIClientError("OpenAI Vision запрос завершился ошибкой") from exc

        content = response.choices[0].message.content or ""
        LOGGER.debug("Vision completion tokens: %s", response.usage)
        return content.strip()

    async def transcribe_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Transcribe short audio payloads (e.g. Telegram voice messages)."""

        buffer = io.BytesIO(audio_bytes)
        buffer.name = filename

        try:
            response = await self._client.audio.transcriptions.create(
                model=self._transcribe_model,
                file=buffer,
                response_format="text",
            )
        except Exception as exc:  # pragma: no cover - network failure
            raise OpenAIClientError("Не удалось распознать голосовое сообщение") from exc

        transcript = getattr(response, "text", "") or ""
        LOGGER.debug("Transcription result length: %s chars", len(transcript))
        return transcript.strip()


