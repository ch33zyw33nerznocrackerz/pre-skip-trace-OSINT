from __future__ import annotations

from service_osint.core.errors import (
    CollectorError,
    ConfigurationError,
    DatabaseError,
    OsintError,
    ProviderError,
    error_dict,
    format_http_error,
    format_osint_error,
    provider_error_message,
)


def test_format_http_error_unauthorized() -> None:
    msg = format_http_error(Exception("HTTP 401 Unauthorized"))
    assert "401" in msg
    assert ".env" in msg


def test_format_http_error_rate_limit() -> None:
    msg = format_http_error(Exception("429 Too Many Requests"))
    assert "rate limit" in msg.lower()


def test_format_http_error_timeout() -> None:
    msg = format_http_error(Exception("ReadTimeout"), context="Serper")
    assert "Serper" in msg
    assert "timed out" in msg.lower()


def test_provider_error_message_includes_provider() -> None:
    msg = provider_error_message("serper", ConnectionError("refused"))
    assert "Serper" in msg


def test_format_osint_error_database() -> None:
    message, hint = format_osint_error(DatabaseError("db down", hint="run doctor"))
    assert message == "db down"
    assert hint == "run doctor"


def test_format_osint_error_provider_default_hint() -> None:
    message, hint = format_osint_error(ProviderError("api fail", provider="brave"))
    assert message == "api fail"
    assert "discover providers" in hint


def test_custom_exception_hierarchy() -> None:
    for cls in (DatabaseError, ConfigurationError, ProviderError, CollectorError):
        assert issubclass(cls, OsintError)


def test_error_dict_minimal() -> None:
    result = error_dict("failed")
    assert result == {"success": False, "error": "failed"}
