from __future__ import annotations

from service_osint.core.db import init_db, table_names, verify_db_connection
from service_osint.core.errors import DatabaseError, format_http_error, error_dict


def test_init_db_creates_tables(isolated_db) -> None:
    assert isolated_db.is_file()
    assert verify_db_connection()
    tables = table_names()
    assert "defendants" in tables
    assert "addresses" in tables


def test_init_db_idempotent(isolated_db) -> None:
    init_db()
    first = set(table_names())
    init_db()
    assert set(table_names()) == first


def test_format_http_error_connection() -> None:
    msg = format_http_error(ConnectionError("Connection refused"))
    assert "Connection refused" in msg
    assert "osint doctor" in msg.lower() or "doctor" in msg


def test_error_dict_shape() -> None:
    result = error_dict("boom", hint="fix it", tool="photon")
    assert result["success"] is False
    assert result["error"] == "boom"
    assert result["hint"] == "fix it"
    assert result["tool"] == "photon"


def test_database_error_has_hint() -> None:
    err = DatabaseError("failed", hint="run doctor")
    assert str(err) == "failed"
    assert err.hint == "run doctor"
