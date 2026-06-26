from __future__ import annotations

from typing import Optional
import typer
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import select

from service_osint.collectors import COLLECTORS, list_collectors, persist_collection, run_collector
from service_osint.core.db import SessionLocal
from service_osint.core.models import CollectionRun, Defendant
from service_osint.cli._helpers import console, get_defendant


def _run_and_save(
    collector: str,
    subject: str,
    *,
    capture: bool,
    wait_ms: int,
    state: str | None,
    city: str | None,
    create: bool,
) -> None:
    try:
        result = run_collector(
            collector,
            subject,
            capture=capture,
            wait_ms=wait_ms,
            state=state,
            city=city,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    with SessionLocal() as s:
        defendant = s.scalar(select(Defendant).where(Defendant.name == subject))
        if not defendant:
            if not create:
                raise typer.BadParameter(
                    f'Subject {subject!r} not found. Add with add-subject or pass --create.'
                )
            defendant = Defendant(name=subject, entity_type="person")
            s.add(defendant)
            s.commit()
            s.refresh(defendant)
            console.print(f"[green]Created subject:[/] {subject}")

        evidence_id, run_id = persist_collection(s, defendant.id, result)

    console.print(Panel(f"[bold]{result.collector}[/] -> {result.url}", title="Collected"))
    if result.screenshot_path:
        console.print(f"[green]Screenshot:[/] {result.screenshot_path}")
        console.print(f"SHA-256: {result.sha256}")
    console.print(f"[dim]Evidence #{evidence_id} · Run #{run_id}[/]")
    if result.extra_urls:
        console.print("\n[bold]Related URLs[/]")
        for u in result.extra_urls:
            console.print(f"  {u}")
    if result.manual_steps:
        console.print("\n[bold]Next steps (manual)[/]")
        for i, step in enumerate(result.manual_steps, 1):
            console.print(f"  {i}. {step}")


def register(collect_app: typer.Typer) -> None:
    @collect_app.command("list")
    def collect_list() -> None:
        """List available public-record collectors."""
        t = Table(title="Collectors")
        t.add_column("Name")
        t.add_column("Description")
        for name, label in list_collectors():
            t.add_row(name, label)
        console.print(t)

    @collect_app.command("runs")
    def collect_runs(name: str) -> None:
        """Show collector run history for a subject."""
        with SessionLocal() as s:
            d = get_defendant(s, name)
            runs = s.scalars(
                select(CollectionRun)
                .where(CollectionRun.defendant_id == d.id)
                .order_by(CollectionRun.created_at.desc())
            ).all()
            if not runs:
                console.print("[dim]No collection runs yet.[/]")
                return
            t = Table(title=f"Collection runs — {name}")
            for col in ["ID", "Collector", "Status", "URL", "Evidence", "When"]:
                t.add_column(col)
            for r in runs:
                t.add_row(
                    str(r.id),
                    r.collector,
                    r.status,
                    r.target_url[:60],
                    str(r.evidence_id or ""),
                    r.created_at.isoformat(),
                )
            console.print(t)

    def _opts(
        capture: bool = typer.Option(True, "--capture/--no-capture", help="Playwright screenshot"),
        wait_ms: int = typer.Option(2500, help="Wait before screenshot (ms)"),
        state: Optional[str] = typer.Option(None, help="State code (property collector)"),
        city: Optional[str] = typer.Option(None, help="City hint for property/socials"),
        create: bool = typer.Option(False, "--create", help="Create subject if missing"),
    ) -> dict:
        return {"capture": capture, "wait_ms": wait_ms, "state": state, "city": city, "create": create}

    @collect_app.command("sec")
    def collect_sec(
        subject: str,
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        wait_ms: int = 2500,
        create: bool = typer.Option(False, "--create"),
    ) -> None:
        """SEC EDGAR + OTC search portal capture."""
        _run_and_save("sec", subject, capture=capture, wait_ms=wait_ms, state=None, city=None, create=create)

    @collect_app.command("nvsos")
    def collect_nvsos(
        subject: str,
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        wait_ms: int = 2500,
        create: bool = typer.Option(False, "--create"),
    ) -> None:
        """Nevada Secretary of State entity search capture."""
        _run_and_save("nvsos", subject, capture=capture, wait_ms=wait_ms, state=None, city=None, create=create)

    @collect_app.command("property")
    def collect_property(
        subject: str,
        state: str = typer.Option("NV", help="US state code (all states; NETR fallback)"),
        city: Optional[str] = None,
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        wait_ms: int = 2500,
        create: bool = typer.Option(False, "--create"),
    ) -> None:
        """County assessor or NETR state directory capture for owner-name search."""
        _run_and_save(
            "property", subject, capture=capture, wait_ms=wait_ms, state=state, city=city, create=create
        )

    @collect_app.command("property-states")
    def collect_property_states() -> None:
        """List property portal routing by state (assessor vs NETR)."""
        from service_osint.collectors.property_portals import list_property_states

        t = Table(title="Property portal routing")
        t.add_column("State")
        t.add_column("Primary portal")
        t.add_column("Type")
        for st, name, typ in list_property_states():
            t.add_row(st, name[:55], typ)
        console.print(t)

    @collect_app.command("court")
    def collect_court(
        subject: str,
        state: Optional[str] = typer.Option(None, help="Narrow CourtListener search by state"),
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        wait_ms: int = 2500,
        create: bool = typer.Option(False, "--create"),
    ) -> None:
        """CourtListener / RECAP federal docket search capture."""
        _run_and_save(
            "court", subject, capture=capture, wait_ms=wait_ms, state=state, city=None, create=create
        )

    @collect_app.command("opencorp")
    def collect_opencorp(
        subject: str,
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        wait_ms: int = 2500,
        create: bool = typer.Option(False, "--create"),
    ) -> None:
        """OpenCorporates officer / registered-agent search capture."""
        _run_and_save("opencorp", subject, capture=capture, wait_ms=wait_ms, state=None, city=None, create=create)

    @collect_app.command("socials")
    def collect_socials(
        subject: str,
        city: Optional[str] = None,
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        wait_ms: int = 2500,
        create: bool = typer.Option(False, "--create"),
    ) -> None:
        """LinkedIn/Facebook people-search entry capture."""
        _run_and_save(
            "socials", subject, capture=capture, wait_ms=wait_ms, state=None, city=city, create=create
        )

    _ = COLLECTORS  # registry reference
