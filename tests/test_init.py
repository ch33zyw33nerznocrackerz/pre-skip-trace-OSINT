from __future__ import annotations

import json

import service_osint
from service_osint.cli.app import app
from service_osint.core.errors import (
    CollectorError,
    ConfigurationError,
    DatabaseError,
    OsintError,
    ProviderError,
)
from service_osint.core.health import REQUIRED_TABLES, health_checks_to_dict


def test_package_version() -> None:
    assert service_osint.__version__ == "0.9.0"


def test_typer_app_registered() -> None:
    command_names = {cmd.name for cmd in app.registered_commands if cmd.name}
    assert "health" in command_names
    assert "keys" in command_names
    assert "doctor" in command_names
    assert "debug-env" in command_names
    assert "run" in command_names


def test_domain_subcommand_registered() -> None:
    from typer.main import get_command

    typer_cmd = get_command(app)
    assert "domain" in typer_cmd.commands


def test_import_core_modules() -> None:
    from service_osint.core import db, env, errors, health, debug  # noqa: F401

    assert db.verify_db_connection.__name__ == "verify_db_connection"
    assert health.run_health_checks.__name__ == "run_health_checks"


def test_error_types_are_osint_errors() -> None:
    for cls in (DatabaseError, ConfigurationError, ProviderError, CollectorError):
        assert issubclass(cls, OsintError)


def test_required_tables_match_schema(isolated_db) -> None:
    from service_osint.core.db import table_names

    tables = set(table_names())
    assert REQUIRED_TABLES.issubset(tables)


def test_health_checks_to_dict_shape(isolated_db) -> None:
    from service_osint.core.health import run_health_checks

    checks = run_health_checks(include_foss=False, include_playwright=False)
    payload = health_checks_to_dict(checks)
    assert payload["status"] in {"ok", "warn", "fail"}
    assert isinstance(payload["checks"], list)
    assert "name" in payload["checks"][0]
    json.dumps(payload)
