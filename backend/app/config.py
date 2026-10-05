"""Application settings, read from environment variables (and a local .env file)."""

import logging
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("lead_manager")

LOCAL_FALLBACK_DB = "sqlite:///./leads.db"
_PLACEHOLDER_MARKERS = ("<your", "your_", "replace_me", "changeme")


def is_placeholder(value: str | None) -> bool:
    """True when a setting is empty or still holds a template placeholder."""
    if not value or not value.strip():
        return True
    lowered = value.strip().lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _normalise_db_url(url: str) -> str:
    # Some hosts (Heroku, older Render/Neon snippets) hand out "postgres://",
    # which SQLAlchemy 2.x no longer accepts.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


@dataclass
class Settings:
    database_url: str
    gemini_api_url: str | None
    gemini_api_key: str | None
    cors_origins: list[str] = field(default_factory=list)

    @property
    def ai_configured(self) -> bool:
        return bool(self.gemini_api_url and self.gemini_api_key)


def load_settings() -> Settings:
    raw_db = os.getenv("DATABASE_URL")
    if is_placeholder(raw_db):
        logger.warning(
            "DATABASE_URL is not set - using local SQLite (%s). "
            "Set DATABASE_URL in backend/.env to use your real database.",
            LOCAL_FALLBACK_DB,
        )
        database_url = LOCAL_FALLBACK_DB
    else:
        database_url = _normalise_db_url(raw_db.strip())

    api_url = os.getenv("GEMINI_API_URL")
    api_key = os.getenv("GEMINI_API_KEY")
    origins = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]

    return Settings(
        database_url=database_url,
        gemini_api_url=None if is_placeholder(api_url) else api_url.strip(),
        gemini_api_key=None if is_placeholder(api_key) else api_key.strip(),
        cors_origins=origins,
    )


settings = load_settings()
