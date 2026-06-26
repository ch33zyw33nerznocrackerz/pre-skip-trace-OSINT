from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select

from service_osint.core.db import SessionLocal
from service_osint.core.models import Alias, Defendant
from service_osint.discovery import list_providers
from service_osint.pipeline import PipelineConfig, preview_plan, run_pipeline
from service_osint.pipeline.planner import default_collectors
from service_osint.domain.utils import domain_from_email
from service_osint.cli._helpers import console


def _ask(text: str, *, default: str = "") -> str:
    return typer.prompt(text, default=default).strip()


def _ask_optional(text: str) -> str | None:
    val = typer.prompt(text, default="").strip()
    return val or None


def _ask_yes(text: str, *, default: bool = True) -> bool:
    return typer.confirm(text, default=default)


def collect_interactive_config() -> PipelineConfig | None:
    """Prompt user for skip-trace details; return None if cancelled."""
    console.print(
        Panel(
            "[bold]Service OSINT[/] — lawful skip-trace assistant\n"
            "Answer the prompts below. The tool will search public records, "
            "run discovery APIs, capture evidence, and build a service packet.",
            title="Welcome",
        )
    )

    # Existing subjects (quick pick)
    with SessionLocal() as s:
        existing = s.scalars(select(Defendant).order_by(Defendant.name).limit(12)).all()
    if existing:
        console.print("\n[dim]Recent subjects:[/] " + ", ".join(d.name for d in existing))

    console.print("\n[bold]1. Subject type[/]")
    entity_raw = _ask("Person or company?", default="person").lower()
    entity_type = "company" if entity_raw.startswith("c") else "person"

    console.print("\n[bold]2. Subject identity[/]")
    name = _ask("Full legal name (required)")
    if not name:
        console.print("[red]Name is required.[/]")
        return None

    role = _ask_optional("Role in case (e.g. Individual defendant, Officer)")
    if entity_type == "person":
        city = _ask_optional("City (recommended)")
        state = _ask_optional("State (2-letter, e.g. NV)")
        phone = _ask_optional("Phone number (optional)")
        email = _ask_optional("Email (optional)")
        employer = _ask_optional("Employer / company tie (optional)")
    else:
        city = _ask_optional("Principal city (optional)")
        state = _ask_optional("State of incorporation (e.g. NV)")
        phone = None
        email = _ask_optional("Contact email on filings (optional)")
        employer = None

    aliases_raw = _ask_optional("Known aliases (comma-separated, optional)")

    console.print("\n[bold]3. Search options[/]")
    ready_providers = [n for n, ok, _ in list_providers() if ok]
    if ready_providers:
        console.print(f"[green]Discovery APIs ready:[/] {', '.join(ready_providers)}")
    else:
        console.print(
            "[yellow]No discovery API keys configured.[/] "
            "Add keys to .env for Serper/Brave/etc. Collectors and dorks still run."
        )

    capture = _ask_yes("Capture Playwright screenshots of portals?", default=True)
    discovery = _ask_yes("Run web discovery APIs (Google-style search)?", default=True)
    dorks = _ask_yes("Run Google dork discovery?", default=True)
    export_packet = _ask_yes("Export HTML/JSON/CSV/PDF packet when done?", default=True)
    foss = _ask_yes(
        "Run FOSS tools (SpiderFoot email/domain, Photon crawl)? Slow — needs Docker or SPIDERFOOT_DIR",
        default=False,
    )
    domain_recon = False
    if email or employer:
        domain_recon = _ask_yes(
            "Run domain/subdomain recon (subfinder, dnsx, httpx)? Best with work email domain",
            default=bool(domain_from_email(email)),
        )
    social_pai = _ask_yes(
        "Run social PAI (Sherlock / holehe / socialscan across platforms)? Needs FOSS_DOCKER or pip tools",
        default=bool(email or phone),
    )

    out_raw = _ask("Output folder", default="out")
    out_dir = Path(out_raw)

    config = PipelineConfig(
        subject=name,
        entity_type=entity_type,
        city=city,
        state=state,
        phone=phone,
        email=email,
        employer=employer,
        role=role,
        capture=capture,
        discovery=discovery,
        dork_discovery=dorks,
        export_packet=export_packet,
        out_dir=out_dir,
        foss=foss,
        domain_recon=domain_recon,
        social_pai=social_pai,
    )

    # Summary + confirm
    collectors = default_collectors(config)
    steps = preview_plan(config)
    summary = Table(title="Search plan — confirm to start")
    summary.add_column("Field")
    summary.add_column("Value")
    summary.add_row("Subject", name)
    summary.add_row("Type", entity_type)
    if city:
        summary.add_row("City", city)
    if state:
        summary.add_row("State", state)
    if phone:
        summary.add_row("Phone", phone)
    if email:
        summary.add_row("Email", email)
    if employer:
        summary.add_row("Employer", employer)
    summary.add_row("Collectors", ", ".join(collectors))
    summary.add_row("Steps", str(len(steps)))
    summary.add_row("Screenshots", "yes" if capture else "no")
    summary.add_row("Discovery", "yes" if discovery else "no")
    summary.add_row("Packet export", "yes" if export_packet else "no")
    summary.add_row("FOSS tools", "yes" if foss else "no")
    summary.add_row("Social PAI", "yes" if social_pai else "no")
    console.print(summary)

    if not _ask_yes("\nStart automatic OSINT search now?", default=True):
        console.print("[dim]Cancelled. Run again with: osint[/]")
        return None

    aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()] if aliases_raw else None
    config.aliases = aliases
    return config


def save_aliases(subject: str, aliases: list[str] | None) -> None:
    if not aliases:
        return
    with SessionLocal() as s:
        d = s.scalar(select(Defendant).where(Defendant.name == subject))
        if not d:
            return
        for alias in aliases:
            exists = s.scalar(
                select(Alias).where(Alias.defendant_id == d.id, Alias.alias == alias)
            )
            if not exists:
                s.add(Alias(defendant_id=d.id, alias=alias))
        s.commit()


def execute_pipeline(config: PipelineConfig) -> None:
    """Run pipeline with progress table (shared by run + interactive)."""
    console.print(f"\n[bold]Searching...[/] {config.subject}")
    t = Table(title="Pipeline progress")
    t.add_column("Step")
    t.add_column("Status")
    t.add_column("Detail")

    def on_step(sr) -> None:
        style = "green" if sr.status == "ok" else ("yellow" if sr.status == "skipped" else "red")
        t.add_row(sr.step, f"[{style}]{sr.status}[/]", sr.detail[:80])
        console.print(f"  [{style}]{sr.step}[/] {sr.detail[:70]}")

    result = run_pipeline(config, on_step=on_step)

    if config.aliases:
        save_aliases(config.subject, config.aliases)

    console.print(t)
    console.print(
        f"\n[bold]Done.[/] evidence+={result.evidence_added} leads+={result.leads_added} "
        f"collectors={result.collectors_run} discovery_hits={result.discovery_hits}"
    )
    if result.packet_paths:
        console.print("[bold]Packet files[/]")
        for kind, path in sorted(result.packet_paths.items()):
            console.print(f"  {kind}: {path.resolve()}")
    console.print(f"\n[dim]Automation run #{result.automation_run_id}[/]")
    console.print("[yellow]Leads are unverified. Corroborate before add-address or service.[/]")
    console.print(
        f"Next steps:\n"
        f"  osint show {config.subject!r}\n"
        f"  osint leads {config.subject!r}\n"
        f"  osint serve-plan {config.subject!r}"
    )


def run_interactive_wizard() -> None:
    config = collect_interactive_config()
    if config is None:
        raise typer.Exit(0)
    execute_pipeline(config)
