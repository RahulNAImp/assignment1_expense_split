"""Gemini client wrapper. Infra failures -> ModelServiceError (spec FR-007, research R5)."""

from __future__ import annotations

from typing import Protocol

from txnsense.config import SETTINGS, Settings


class ModelServiceError(RuntimeError):
    """Model/service failure (quota, 5xx, timeout, missing key): not an application failure."""


class LLMClient(Protocol):
    model: str

    def generate(self, system: str, user: str) -> str: ...


class GeminiClient:
    def __init__(self, settings: Settings = SETTINGS) -> None:
        from google import genai
        from google.genai import types

        key = settings.api_key()
        if not key:
            raise ModelServiceError("GEMINI_API_KEY is not set (see .env.example)")
        self._types = types
        self.model = settings.model
        self.temperature = settings.temperature
        self._client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=settings.timeout_ms,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    def generate(self, system: str, user: str) -> str:
        from google.genai import errors

        try:
            resp = self._client.models.generate_content(
                model=self.model,
                contents=user,
                config=self._types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self.temperature,
                    response_mime_type="application/json",
                ),
            )
        except errors.ServerError as exc:
            raise ModelServiceError(f"server error: {exc.code}") from exc
        except errors.ClientError as exc:
            if exc.code in (408, 429):
                raise ModelServiceError(f"rate limited / timeout: {exc.code}") from exc
            raise
        except Exception as exc:  # network / timeout from the HTTP layer
            if "timeout" in type(exc).__name__.lower() or "connect" in str(exc).lower():
                raise ModelServiceError(f"network: {type(exc).__name__}") from exc
            raise
        return resp.text or ""
