from __future__ import annotations

import json
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from service_osint.core.debug import collect_debug_report, remediation_commands
from service_osint.core.errors import DatabaseError
from service_osint.core.health import (
    HealthCheck,
    health_checks_to_dict,
    overall_status,
    run_health_checks,
)
from service_osint.cli._helpers import console, get_debug
from service_osint.cli.keys_display import print_api_keys_report


def _status_style(status: str) -> str:
    return {"ok": "green", "warn": "yellow", "fail": "red"}.get(status, "white")


def _print_checks(checks: list[HealthCheck], *, verbose: bool = False) -> str:
    t = Table(title="Health Checks")
    t.add_column("Check")
    t.add_column("Status")
    t.add_column("Message")
    if verbose:
        t.add_column("ms")
    for check in checks:
        row = [
            check.name,
            f"[{_status_style(check.status)}]{check.status}[/]",
            check.message,
        ]
        if verbose:
            row.append(str(check.duration_ms))
        t.add_row(*row)
        if check.hint and check.status != "ok":
            console.print(f"  [dim]-> {check.hint}[/]")
        if verbose and check.details:
            for key, value in check.details.items():
                console.print(f"    [dim]{key}:[/] {value}")
    console.print(t)
    return overall_status(checks)


def register(app: typer.Typer) -> None:
    @app.command("health")
    def health_cmd(
        ctx: typer.Context,
        init: bool = typer.Option(False, "--init", help="Create DB tables if missing"),
        probe_searxng: bool = typer.Option(False, "--probe-searxng", help="HTTP probe SearXNG"),
        verbose: bool = typer.Option(False, "--verbose", "-v"),
        json_out: bool = typer.Option(False, "--json", help="Machine-readable output"),
    ) -> None:
        """Quick startup health check (DB, env, discovery, Docker)."""
        debug = get_debug(ctx)
        try:
            checks = run_health_checks(
                init_db_if_missing=init,
                probe_searxng=probe_searxng,
                include_foss=not json_out,
                include_playwright=False,
            )
        except DatabaseError as exc:
            console.print(f"[red]Database error:[/] {exc}")
            if exc.hint:
                console.print(f"[dim]{exc.hint}[/]")
            if debug:
                raise
            raise typer.Exit(1) from exc

        if json_out:
            payload = health_checks_to_dict(checks)
            console.print(json.dumps(payload, indent=2))
            if payload["status"] == "fail":
                raise typer.Exit(1)
            return

        status = _print_checks(checks, verbose=verbose)
        if status == "ok":
            console.print("[green]All checks passed.[/]")
        elif status == "warn":
            console.print("[yellow]Checks passed with warnings — run `osint doctor` for details.[/]")
        else:
            console.print("[red]Some checks failed — run `osint doctor` for remediation steps.[/]")
            raise typer.Exit(1)

    @app.command("doctor")
    def doctor_cmd(
        probe_searxng: bool = typer.Option(True, "--probe-searxng/--no-probe-searxng"),
        init: bool = typer.Option(True, "--init/--no-init", help="Initialize DB if needed"),
    ) -> None:
        """Verbose diagnostics with step-by-step remediation hints."""
        report = collect_debug_report(probe_searxng=probe_searxng, init_db_if_missing=init)

        console.print(
            Panel(
                f"[bold]service-osint {report.version}[/]\n"
                f"{report.platform}\n"
                f"cwd: {report.cwd}\n"
                f"env: {report.env_file or '(none)'}",
                title="Debug Report",
            )
        )

        for step in report.steps:
            style = _status_style(step.status)
            console.print(f"\n[bold]{step.step}. {step.title}[/] [{style}]{step.status}[/]")
            console.print(f"   {step.detail}")
            if step.action:
                console.print(f"   [cyan]-> {step.action}[/]")

        status = overall_status(report.health)
        console.print()
        print_api_keys_report(missing_only=True)
        console.print()
        fixes = remediation_commands(report.health)
        if fixes:
            console.print("[bold]Suggested fixes:[/]")
            for cmd in fixes:
                console.print(f"  [cyan]$ {cmd}[/]")
            console.print()
        if status == "fail":
            console.print("[red]Doctor found blocking issues.[/] Fix failures above, then re-run.")
            raise typer.Exit(1)
        if status == "warn":
            console.print("[yellow]Environment is usable but some optional components need attention.[/]")
        else:
            console.print("[green]Environment looks healthy.[/]")

    @app.command("keys")
    def keys_cmd(
        missing_only: bool = typer.Option(False, "--missing", "-m", help="Show only missing keys"),
        json_out: bool = typer.Option(False, "--json", help="Machine-readable output"),
    ) -> None:
        """List API keys: configured vs missing, with free/paid tier and signup URLs."""
        print_api_keys_report(missing_only=missing_only, json_out=json_out)

    @app.command("debug-env")
    def debug_env_cmd() -> None:
        """Print masked environment configuration (no secrets)."""
        from service_osint.core.env import env_summary, find_env_file

        path = find_env_file()
        console.print(f"Env file: {path or '(not found)'}")
        t = Table()
        t.add_column("Variable")
        t.add_column("Value")
        for key, value in env_summary().items():
            t.add_row(key, value)
        console.print(t)
