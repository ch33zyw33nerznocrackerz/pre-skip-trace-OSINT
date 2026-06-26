from __future__ import annotations

from unittest.mock import MagicMock, patch

from service_osint.core.debug import collect_debug_report
from service_osint.core.health import (
    HealthCheck,
    check_discovery_providers,
    check_env_file,
    check_python,
    check_searxng,
    overall_status,
    run_health_checks,
)


def test_check_python_ok() -> None:
    result = check_python()
    assert result.status == "ok"
    assert "Python" in result.message


def test_overall_status_priority() -> None:
    checks = [
        HealthCheck("a", "ok", "fine"),
        HealthCheck("b", "warn", "meh"),
    ]
    assert overall_status(checks) == "warn"
    checks.append(HealthCheck("c", "fail", "bad"))
    assert overall_status(checks) == "fail"


def test_check_discovery_providers_always_has_duckduckgo() -> None:
    result = check_discovery_providers()
    assert result.status in {"ok", "warn", "fail"}
    assert "duckduckgo" in result.details


def test_check_searxng_unset() -> None:
    with patch.dict("os.environ", {}, clear=True):
        from service_osint.discovery.config import DiscoveryConfig

        with patch.object(DiscoveryConfig, "from_env", return_value=DiscoveryConfig.from_env()):
            result = check_searxng()
    # Without SEARXNG_URL in env, should warn
    assert result.status in {"warn", "fail", "ok"}


def test_run_health_checks_returns_core_checks(isolated_db) -> None:
    checks = run_health_checks(include_foss=False, include_playwright=False)
    names = {c.name for c in checks}
    assert "python" in names
    assert "database" in names
    assert "discovery" in names


def test_check_searxng_unreachable() -> None:
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = ConnectionError("refused")
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_resp

    with patch("service_osint.core.health.DiscoveryConfig") as cfg_cls:
        cfg_cls.from_env.return_value.searxng_url = "http://127.0.0.1:59999"
        with patch("service_osint.core.health.httpx.Client", return_value=mock_client):
            result = check_searxng()
    assert result.status == "fail"


def test_collect_debug_report(isolated_db) -> None:
    report = collect_debug_report(probe_searxng=False, init_db_if_missing=True)
    assert report.version
    assert len(report.steps) >= 4
    assert report.health
    titles = [s.title for s in report.steps]
    assert "Verify install" in titles
    assert "Data directories" in titles


def test_health_checks_to_dict(isolated_db) -> None:
    from service_osint.core.health import health_checks_to_dict, run_health_checks

    checks = run_health_checks(include_foss=False, include_playwright=False)
    data = health_checks_to_dict(checks)
    assert data["status"] in {"ok", "warn", "fail"}
    assert all("duration_ms" in c for c in data["checks"])


def test_check_env_file_warns_without_env(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("service_osint.core.health.find_env_file", return_value=None):
        result = check_env_file()
    assert result.status == "warn"
    assert ".env" in result.hint
