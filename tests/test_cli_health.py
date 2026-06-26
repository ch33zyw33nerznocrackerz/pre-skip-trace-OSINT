from __future__ import annotations

from typer.testing import CliRunner

from service_osint.cli.app import app

runner = CliRunner()


def test_health_command_json(isolated_db, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["health", "--json", "--init"])
    assert result.exit_code in {0, 1}
    assert "checks" in result.stdout
    assert "python" in result.stdout


def test_debug_env_command(isolated_db, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("SEARXNG_URL=http://127.0.0.1:8080\n", encoding="utf-8")
    result = runner.invoke(app, ["debug-env"])
    assert result.exit_code == 0
    assert "SEARXNG_URL" in result.stdout


def test_doctor_command_smoke(isolated_db, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor", "--no-probe-searxng", "--init"])
    assert result.exit_code in {0, 1}
    assert "Debug Report" in result.stdout
    assert "service-osint" in result.stdout


def test_health_verbose_flag(isolated_db, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["health", "--verbose", "--init"])
    assert result.exit_code in {0, 1}
    assert "Health Checks" in result.stdout
