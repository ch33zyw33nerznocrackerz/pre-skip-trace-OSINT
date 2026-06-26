from __future__ import annotations

from typing import Any


class OsintError(Exception):
    """Base error for recoverable OSINT failures."""

    def __init__(self, message: str, *, hint: str = "") -> None:
        super().__init__(message)
        self.hint = hint


class ConfigurationError(OsintError):
    """Missing or invalid configuration."""


class DatabaseError(OsintError):
    """SQLite / SQLAlchemy failures."""


class ProviderError(OsintError):
    """Discovery or external API provider failure."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        hint: str = "",
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.provider = provider
        self.cause = cause


class CollectorError(OsintError):
    """Collector pipeline failure."""


def format_http_error(exc: BaseException, *, context: str = "") -> str:
    """Turn httpx/network errors into actionable CLI messages."""
    prefix = f"{context}: " if context else ""
    name = type(exc).__name__
    message = str(exc).strip() or name

    lowered = message.lower()
    if "connect" in lowered or "connection refused" in lowered:
        hint = "Service may be down — run `osint doctor` to verify."
        return f"{prefix}{message} ({hint})"
    if "timeout" in lowered or name in {"ReadTimeout", "ConnectTimeout", "WriteTimeout"}:
        return f"{prefix}Request timed out — check network or increase provider timeout."
    if "401" in message or "unauthorized" in lowered:
        return f"{prefix}{message} — verify API key in .env."
    if "403" in message or "forbidden" in lowered:
        return f"{prefix}{message} — API key may lack permissions or quota exceeded."
    if "404" in message or "not found" in lowered:
        return f"{prefix}{message} — check endpoint URL (e.g. SEARXNG_URL)."
    if "429" in message or "rate limit" in lowered:
        return f"{prefix}{message} — rate limited; retry later or switch provider."
    if "500" in message or "502" in message or "503" in message:
        return f"{prefix}{message} — upstream service error; retry later."
    return f"{prefix}{message}"


def provider_error_message(provider: str, exc: BaseException) -> str:
    """Standard discovery-provider error string for DiscoveryResult.error."""
    label = provider.replace("_", " ").title()
    return format_http_error(exc, context=label)


def format_osint_error(exc: BaseException) -> tuple[str, str]:
    """Return (message, hint) for CLI display of OsintError subclasses."""
    if isinstance(exc, ProviderError):
        hint = exc.hint or "Run `osint discover providers` to verify configuration."
        return str(exc), hint
    if isinstance(exc, OsintError):
        return str(exc), exc.hint
    return str(exc), "Re-run with `osint --debug` for a full traceback."


def error_dict(
    message: str,
    *,
    hint: str = "",
    **extra: Any,
) -> dict[str, Any]:
    """Standard error payload for tool runners and collectors."""
    out: dict[str, Any] = {"success": False, "error": message}
    if hint:
        out["hint"] = hint
    out.update(extra)
    return out
