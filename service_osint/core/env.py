from __future__ import annotations

import os
from pathlib import Path

_ENV_LOADED_FROM: Path | None = None

_MASKED_KEYS = frozenset(
    {
        "SERPER_API_KEY",
        "TAVILY_API_KEY",
        "EXA_API_KEY",
        "BRAVE_API_KEY",
        "BRAVE_SEARCH_API_KEY",
        "LINKUP_API_KEY",
        "FIRECRAWL_API_KEY",
        "JINA_API_KEY",
        "CHAOS_API_KEY",
        "COURTLISTENER_API_TOKEN",
        "OPENCORPORATES_API_TOKEN",
    }
)

_TRACKED_KEYS = (
    "SEARXNG_URL",
    "SERPER_API_KEY",
    "TAVILY_API_KEY",
    "EXA_API_KEY",
    "BRAVE_API_KEY",
    "LINKUP_API_KEY",
    "FIRECRAWL_API_KEY",
    "JINA_API_KEY",
    "FOSS_DOCKER",
    "CHAOS_API_KEY",
    "COURTLISTENER_API_TOKEN",
    "OPENCORPORATES_API_TOKEN",
    "SEC_CONTACT_EMAIL",
)


def env_candidates() -> list[Path]:
    return [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]


def find_env_file() -> Path | None:
    for path in env_candidates():
        if path.is_file():
            return path
    return None


def loaded_env_path() -> Path | None:
    return _ENV_LOADED_FROM


def load_env() -> Path | None:
    """Load .env from cwd or project root (first match wins). Returns path loaded."""
    global _ENV_LOADED_FROM
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None

    for path in env_candidates():
        if path.is_file():
            load_dotenv(path, override=False)
            _ENV_LOADED_FROM = path
            return path
    load_dotenv(override=False)
    _ENV_LOADED_FROM = None
    return None


def env_summary() -> dict[str, str]:
    """Return tracked env vars with values masked for debug output."""
    out: dict[str, str] = {}
    for key in _TRACKED_KEYS:
        value = os.getenv(key)
        if not value:
            out[key] = "(unset)"
        elif key in _MASKED_KEYS:
            out[key] = "(set)"
        else:
            out[key] = value
    return out
