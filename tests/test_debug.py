from __future__ import annotations

from service_osint.core.debug import remediation_commands
from service_osint.core.health import HealthCheck, overall_status


def test_remediation_commands_for_missing_env() -> None:
    health = [
        HealthCheck("env_file", "warn", "missing", hint="copy .env"),
        HealthCheck("database", "ok", "fine"),
        HealthCheck("discovery", "ok", "fine"),
    ]
    cmds = remediation_commands(health)
    assert "copy .env.example .env" in cmds


def test_remediation_commands_dedupes() -> None:
    health = [
        HealthCheck("searxng", "fail", "down"),
        HealthCheck("discovery", "fail", "none"),
    ]
    cmds = remediation_commands(health)
    docker_cmds = [c for c in cmds if "docker compose" in c]
    assert len(docker_cmds) == 1


def test_remediation_empty_when_healthy() -> None:
    health = [HealthCheck("python", "ok", "3.12")]
    assert remediation_commands(health) == []


def test_overall_status_all_ok() -> None:
    assert overall_status([HealthCheck("a", "ok", "")]) == "ok"
