from __future__ import annotations

from pathlib import Path
from typing import Optional
import typer
from rich.table import Table
from sqlalchemy import select

from service_osint.capture import screenshot_url
from service_osint.core.db import SessionLocal
from service_osint.core.models import Address, Alias, Defendant, Evidence, ServiceAttempt
from service_osint.core.scoring import score_address
from service_osint.cli._helpers import console, get_defendant


def register(app: typer.Typer) -> None:
    @app.command("add-subject")
    def add_subject(
        name: str,
        role: Optional[str] = None,
        entity_type: str = "person",
        notes: Optional[str] = None,
    ) -> None:
        """Add an individual (or entity) to track for skip-trace / service."""
        with SessionLocal() as s:
            existing = s.scalar(select(Defendant).where(Defendant.name == name))
            if existing:
                console.print(f"[yellow]Exists:[/] {name}")
                return
            s.add(Defendant(name=name, role=role, entity_type=entity_type, notes=notes))
            s.commit()
            console.print(f"[green]Added subject:[/] {name}")

    @app.command("add-defendant")
    def add_defendant(
        name: str,
        role: Optional[str] = None,
        entity_type: str = "person",
        notes: Optional[str] = None,
    ) -> None:
        """Alias for add-subject (legal dossier naming)."""
        add_subject(name, role=role, entity_type=entity_type, notes=notes)

    @app.command("add-alias")
    def add_alias(name: str, alias: str) -> None:
        with SessionLocal() as s:
            d = get_defendant(s, name)
            s.add(Alias(defendant_id=d.id, alias=alias))
            s.commit()
            console.print(f"[green]Added alias:[/] {alias} -> {name}")

    @app.command("add-address")
    def add_address(
        name: str,
        address: str,
        source: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        confidence: int = typer.Option(50, min=0, max=100),
        corroborations: int = typer.Option(0, min=0, max=10),
        recent: bool = False,
        last_seen: Optional[str] = None,
        tags: Optional[str] = typer.Option(None, help="Comma tags: residence,office,gated,mailing,old"),
        notes: Optional[str] = None,
    ) -> None:
        with SessionLocal() as s:
            d = get_defendant(s, name)
            final_score = score_address(confidence, source, corroborations, recent)
            s.add(
                Address(
                    defendant_id=d.id,
                    address=address,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    source=source,
                    confidence=final_score,
                    last_seen=last_seen,
                    tags=tags,
                    notes=notes,
                )
            )
            s.commit()
            console.print(f"[green]Added address:[/] {address} score={final_score}")

    @app.command("add-evidence")
    def add_evidence(
        name: str,
        source_name: str,
        url: str,
        notes: Optional[str] = None,
        file_path: Optional[Path] = None,
        sha256: Optional[str] = None,
    ) -> None:
        with SessionLocal() as s:
            d = get_defendant(s, name)
            s.add(
                Evidence(
                    defendant_id=d.id,
                    source_name=source_name,
                    url=url,
                    notes=notes,
                    file_path=str(file_path) if file_path else None,
                    sha256=sha256,
                )
            )
            s.commit()
            console.print(f"[green]Added evidence:[/] {source_name}")

    @app.command("capture")
    def capture(
        name: str,
        source_name: str,
        url: str,
        notes: Optional[str] = None,
        wait_ms: int = 1500,
    ) -> None:
        """Screenshot a public source URL and attach it as evidence."""
        with SessionLocal() as s:
            d = get_defendant(s, name)
            path, digest = screenshot_url(url, f"{name}-{source_name}", wait_ms=wait_ms)
            s.add(
                Evidence(
                    defendant_id=d.id,
                    source_name=source_name,
                    url=url,
                    notes=notes,
                    file_path=str(path),
                    sha256=digest,
                )
            )
            s.commit()
            console.print(f"[green]Captured:[/] {path}")
            console.print(f"SHA-256: {digest}")

    @app.command("attempt")
    def service_attempt(
        name: str,
        attempted_at: str,
        result: str,
        address_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> None:
        with SessionLocal() as s:
            d = get_defendant(s, name)
            s.add(
                ServiceAttempt(
                    defendant_id=d.id,
                    address_id=address_id,
                    attempted_at=attempted_at,
                    result=result,
                    server_notes=notes,
                )
            )
            s.commit()
            console.print(f"[green]Recorded attempt:[/] {attempted_at} {result}")

    @app.command("show")
    def show(name: str) -> None:
        with SessionLocal() as s:
            d = get_defendant(s, name)
            console.print(f"\n[bold]{d.name}[/]  {d.role or ''}  ({d.entity_type})")
            if d.aliases:
                console.print("[bold]Aliases:[/] " + ", ".join(a.alias for a in d.aliases))

            t = Table(title="Addresses")
            for col in ["ID", "Score", "Address", "City", "State", "ZIP", "Source", "Last Seen", "Tags", "Notes"]:
                t.add_column(col)
            for a in sorted(d.addresses, key=lambda x: x.confidence, reverse=True):
                t.add_row(
                    str(a.id),
                    str(a.confidence),
                    a.address,
                    a.city or "",
                    a.state or "",
                    a.postal_code or "",
                    a.source,
                    a.last_seen or "",
                    a.tags or "",
                    a.notes or "",
                )
            console.print(t)

            e = Table(title="Evidence")
            for col in ["ID", "Source", "URL", "Captured", "File", "SHA-256", "Notes"]:
                e.add_column(col)
            for ev in d.evidence:
                e.add_row(
                    str(ev.id),
                    ev.source_name,
                    ev.url,
                    ev.captured_at.isoformat(),
                    ev.file_path or "",
                    ev.sha256 or "",
                    ev.notes or "",
                )
            console.print(e)

            at = Table(title="Due Diligence / Service Attempts")
            for col in ["ID", "Address ID", "Attempted At", "Result", "Notes"]:
                at.add_column(col)
            for x in d.attempts:
                at.add_row(str(x.id), str(x.address_id or ""), x.attempted_at, x.result, x.server_notes or "")
            console.print(at)

    @app.command("serve-plan")
    def serve_plan(name: str) -> None:
        """Print a practical first-attempt plan from address scores/tags."""
        with SessionLocal() as s:
            d = get_defendant(s, name)
            addrs = sorted(d.addresses, key=lambda x: x.confidence, reverse=True)
            console.print(f"[bold]Serve plan for {d.name}[/]")
            if not addrs:
                console.print("[red]No addresses yet.[/]")
                return
            for idx, a in enumerate(addrs[:5], start=1):
                tags = (a.tags or "").lower()
                windows = ["weekday 6:30-8:30 AM", "weekday 6:00-9:00 PM", "Saturday 9:00-11:30 AM"]
                if "office" in tags:
                    windows = ["weekday 9:00-11:30 AM", "weekday 1:30-4:00 PM"]
                if "gated" in tags:
                    windows.append("coordinate gate/concierge strategy; document access denial")
                console.print(
                    f"\n{idx}. Address ID {a.id} - score {a.confidence}: {a.address}, {a.city or ''} {a.state or ''}"
                )
                console.print("   Windows: " + "; ".join(windows))
                console.print("   Notes: " + (a.notes or "verify identity before attempt"))
