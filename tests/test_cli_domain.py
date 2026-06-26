from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from service_osint.cli.app import app

runner = CliRunner()


def test_domain_resolve_command() -> None:
    result = runner.invoke(app, ["domain", "resolve", "--email", "jane@acmecorp.com"])
    assert result.exit_code == 0
    assert "acmecorp.com" in result.stdout


def test_domain_resolve_rejects_free_email() -> None:
    result = runner.invoke(app, ["domain", "resolve", "--email", "jane@gmail.com"])
    assert result.exit_code == 1


def test_domain_scan_dry_run(isolated_db, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("service_osint.domain.recon.run_foss_tool") as mock_run:
        mock_run.return_value = {"success": True, "dry_run": True}
        result = runner.invoke(app, ["domain", "scan", "acmecorp.com", "--dry-run"])
    assert result.exit_code == 0
    assert mock_run.call_count >= 3


def test_domain_tools_listed() -> None:
    from service_osint.foss import list_foss_tools

    ids = {t.id for t in list_foss_tools(category="domain_recon")}
    assert "subfinder" in ids
    assert "dnsx" in ids
    assert "httpx-pd" in ids
