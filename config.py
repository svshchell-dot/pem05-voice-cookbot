import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


@dataclass(slots=True)
class Settings:
    """Container for application configuration."""

    telegram_token: str
    openai_api_key: str
    openai_text_model: str
    openai_vision_model: str
    openai_transcribe_model: str
    webapp_host: str
    webapp_port: int
    webapp_url: str
    miniapp_path: Path
    database_path: Path


def _load_from_env() -> Settings:
    load_dotenv()

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_text_model = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")
    openai_vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")
    openai_transcribe_model = os.getenv(
        "OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"
    )
    webapp_host = os.getenv("WEBAPP_HOST", "127.0.0.1")
    webapp_port = int(os.getenv("WEBAPP_PORT", "8080"))
    webapp_url = os.getenv("WEBAPP_URL", "")
    miniapp_path = Path(os.getenv("WEBAPP_STATIC_DIR", BASE_DIR / "miniapp")).resolve()
    database_path = Path(os.getenv("DATABASE_PATH", BASE_DIR / "recipes.db")).resolve()

    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", telegram_token),
            ("OPENAI_API_KEY", openai_api_key),
        )
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Отсутствуют обязательные переменные окружения: "
            + ", ".join(missing)
        )

    return Settings(
        telegram_token=telegram_token,
        openai_api_key=openai_api_key,
        openai_text_model=openai_text_model,
        openai_vision_model=openai_vision_model,
        openai_transcribe_model=openai_transcribe_model,
        webapp_host=webapp_host,
        webapp_port=webapp_port,
        webapp_url=webapp_url,
        miniapp_path=miniapp_path,
        database_path=database_path,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Lazy configuration loader with caching."""

    return _load_from_env()

