from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from service_osint.core.db import SessionLocal
from service_osint.pipeline import PipelineConfig
from service_osint.pipeline.store import add_evidence_url, ensure_subject, persist_leads
from service_osint.social import guess_usernames, run_social_pai, social_tools_for_config
from service_osint.foss import check_tool_available, list_foss_tools, use_docker_foss
from service_osint.cli._helpers import console


def register(app: typer.Typer) -> None:
    social_app = typer.Typer(
        help="Social PAI — discover public profiles across networks (Sherlock, holehe, etc.)",
    )
    app.add_typer(social_app, name="social")

    @social_app.command("tools")
    def social_tools() -> None:
        """List social-network discovery tools and availability."""
        mode = "docker" if use_docker_foss() else "local"
        console.print(f"[bold]Social PAI tools[/] (mode: {mode})")
        for tool in list_foss_tools():
            if tool.category not in {"username", "email", "phone"}:
                continue
            ok, detail = check_tool_available(tool)
            style = "green" if ok else "yellow"
            console.print(f"  [{style}]{tool.id}[/] — {tool.name} ({detail})")

    @social_app.command("usernames")
    def social_usernames(
        name: str,
        email: Optional[str] = typer.Option(None, "--email", "-e"),
    ) -> None:
        """Show username candidates generated from name and email."""
        guesses = guess_usernames(name, email)
        if not guesses:
            console.print("[yellow]No username candidates generated.[/]")
            return
        console.print(f"[bold]Username guesses for {name}[/]")
        for i, u in enumerate(guesses, 1):
            console.print(f"  {i}. {u}")

    @social_app.command("scan")
    def social_scan(
        name: str,
        email: Optional[str] = typer.Option(None, "--email", "-e"),
        phone: Optional[str] = typer.Option(None, "--phone", "-p"),
        username: Optional[str] = typer.Option(None, "--username", "-u", help="Override primary username"),
        full: bool = typer.Option(False, "--full", help="Include Maigret (slower, richer metadata)"),
        create: bool = typer.Option(False, "--create", help="Create subject and persist profiles as leads"),
        out: Path = typer.Option(Path("out"), "--out", "-o"),
    ) -> None:
        """Run social PAI scan across platforms from username, email, and/or phone seeds."""
        config = PipelineConfig(subject=name, email=email, phone=phone)
        console.print(f"[bold]Social PAI scan[/] — {name}")
        planned = social_tools_for_config(config, full=full)
        console.print(f"  Planned tools: {len(planned)} ({'full' if full else 'fast'} mode)")

        pai = run_social_pai(
            config,
            out_dir=out / "social",
            full=full,
            username_override=username,
        )

        console.print(
            f"  Tools run: {pai.tools_run}  skipped: {pai.tools_skipped}  "
            f"profiles: {len(pai.profiles)}"
        )
        if pai.errors:
            for err in pai.errors[:5]:
                console.print(f"  [dim]skip:[/] {err}")

        if pai.profiles:
            console.print("[bold]Discovered profiles (leads — verify before service)[/]")
            for url in sorted(pai.profiles)[:40]:
                console.print(f"  {url}")
            if len(pai.profiles) > 40:
                console.print(f"  … and {len(pai.profiles) - 40} more")
        else:
            console.print("[yellow]No profile URLs extracted. Try --full or add --email/--phone.[/]")

        if create and pai.profiles:
            with SessionLocal() as s:
                defendant = ensure_subject(s, config)
                for url in pai.profiles:
                    add_evidence_url(s, defendant.id, "social/pai", url, notes="Social PAI discovery")
                n = persist_leads(s, defendant.id, {"social": pai.profiles}, "social/pai")
                console.print(f"[green]Persisted[/] {len(pai.profiles)} profiles, {n} new leads for {defendant.name}")
