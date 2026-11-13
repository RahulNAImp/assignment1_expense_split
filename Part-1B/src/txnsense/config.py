"""Runtime configuration from environment (Constitution VI). The API key is never logged."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    model: str = os.environ.get("TXNSENSE_MODEL", "gemini-3.5-flash-lite")
    temperature: float = float(os.environ.get("TXNSENSE_TEMPERATURE", "0.2"))
    timeout_ms: int = int(os.environ.get("TXNSENSE_TIMEOUT_MS", "30000"))

    @staticmethod
    def api_key() -> str | None:
        return os.environ.get("GEMINI_API_KEY")


SETTINGS = Settings()
