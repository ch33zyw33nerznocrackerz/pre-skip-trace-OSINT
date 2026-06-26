from __future__ import annotations

from pathlib import Path
from typing import Optional
import typer
from rich.table import Table
from sqlalchemy import select

from service_osint.core.db import SessionLocal
from service_osint.core.models import AutomationRun, Lead
from service_osint.pipeline import PipelineConfig, preview_plan, run_pipeline
from service_osint.cli._helpers import console, get_defendant
from service_osint.cli.interactive import execute_pipeline


def register(app: typer.Typer) -> None:
    @app.command("start")
    def start_interactive() -> None:
        """Interactive wizard: prompt for subject info, then search automatically."""
        from service_osint.cli.interactive import run_interactive_wizard

        run_interactive_wizard()

    @app.command("run")
    def run_full(
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        employer: Optional[str] = None,
        entity_type: str = typer.Option("person", help="person or company"),
        role: Optional[str] = None,
        capture: bool = typer.Option(True, "--capture/--no-capture"),
        discovery: bool = typer.Option(True, "--discovery/--no-discovery"),
        dorks: bool = typer.Option(True, "--dorks/--no-dorks", help="Run dork-based discovery"),
        collectors: Optional[str] = typer.Option(
            None,
            help="Comma collectors: sec,nvsos,opencorp,property,court,socials,people (default auto)",
        ),
        out: Path = typer.Option(Path("out"), help="Packet output directory"),
        formats: str = typer.Option("html,json,csv,pdf", help="Packet formats"),
        no_export: bool = typer.Option(False, "--no-export", help="Skip packet export"),
        foss: bool = typer.Option(False, "--foss", help="Run SpiderFoot/Photon (Docker or local)"),
        domain_recon: bool = typer.Option(
            False,
            "--domain-recon",
            help="Enumerate subdomains + probe hosts (subfinder/dnsx/httpx via FOSS_DOCKER)",
        ),
        domain: Optional[str] = typer.Option(
            None,
            "--domain",
            help="Explicit domain for FOSS/domain-recon (else derived from email)",
        ),
        social_pai: bool = typer.Option(
            False, "--social-pai", help="Run social PAI (Sherlock, holehe, etc.) across platforms"
        ),
        wait_ms: int = 2500,
    ) -> None:
        """Full OSINT automation: dorks, discovery APIs, collectors, leads, packet."""
        fmt_set = {f.strip().lower() for f in formats.split(",") if f.strip()}
        coll_list = [c.strip() for c in collectors.split(",")] if collectors else None
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
            wait_ms=wait_ms,
            discovery=discovery,
            dork_discovery=dorks,
            collectors=coll_list,
            export_packet=not no_export,
            packet_formats=fmt_set,
            out_dir=out,
            foss=foss,
            domain=domain,
            domain_recon=domain_recon,
            social_pai=social_pai,
        )
        execute_pipeline(config)

    @app.command("run-plan")
    def run_plan(
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        entity_type: str = "person",
        collectors: Optional[str] = None,
    ) -> None:
        """Preview automation steps without executing."""
        coll_list = [c.strip() for c in collectors.split(",")] if collectors else None
        config = PipelineConfig(
            subject=name,
            entity_type=entity_type,
            city=city,
            state=state,
            collectors=coll_list,
        )
        steps = preview_plan(config)
        console.print(f"[bold]Pipeline plan for {name}[/] ({entity_type})")
        for i, step in enumerate(steps, 1):
            console.print(f"  {i}. {step}")

    @app.command("leads")
    def list_leads(name: str, verified_only: bool = False) -> None:
        """Show auto-extracted leads (phones, emails, address hints)."""
        with SessionLocal() as s:
            d = get_defendant(s, name)
            q = select(Lead).where(Lead.defendant_id == d.id).order_by(Lead.confidence.desc())
            if verified_only:
                q = q.where(Lead.verified.is_(True))
            rows = s.scalars(q).all()
            if not rows:
                console.print("[dim]No leads yet. Run: osint start[/]")
                return
            t = Table(title=f"Leads — {name} (unverified until you add-address)")
            for col in ["ID", "Type", "Value", "Conf", "Source", "Verified"]:
                t.add_column(col)
            for r in rows:
                t.add_row(
                    str(r.id),
                    r.lead_type,
                    r.value[:60],
                    str(r.confidence),
                    r.source,
                    "yes" if r.verified else "no",
                )
            console.print(t)

    @app.command("runs")
    def automation_runs(name: str) -> None:
        """Show automation run history for a subject."""
        with SessionLocal() as s:
            d = get_defendant(s, name)
            rows = s.scalars(
                select(AutomationRun)
                .where(AutomationRun.defendant_id == d.id)
                .order_by(AutomationRun.created_at.desc())
            ).all()
            if not rows:
                console.print("[dim]No automation runs yet.[/]")
                return
            t = Table(title=f"Automation runs — {name}")
            t.add_column("ID")
            t.add_column("Status")
            t.add_column("Started")
            t.add_column("Finished")
            for r in rows:
                t.add_row(
                    str(r.id),
                    r.status,
                    r.created_at.isoformat(),
                    r.finished_at.isoformat() if r.finished_at else "",
                )
            console.print(t)

    _ = run_pipeline  # re-export path for tests
