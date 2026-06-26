from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from service_osint.core.db import SessionLocal
from service_osint.domain import resolve_scan_domain, run_domain_recon
from service_osint.pipeline.store import add_evidence_url, ensure_subject, persist_leads
from service_osint.pipeline.types import PipelineConfig
from service_osint.cli._helpers import console, get_debug, get_defendant


def register(app: typer.Typer) -> None:
    domain_app = typer.Typer(help="Domain/subdomain recon (ProjectDiscovery: subfinder, dnsx, httpx, tlsx)")
    app.add_typer(domain_app, name="domain")

    @domain_app.command("scan")
    def domain_scan(
        ctx: typer.Context,
        domain: Optional[str] = typer.Argument(None, help="Domain to scan (e.g. acmecorp.com)"),
        email: Optional[str] = typer.Option(None, "--email", "-e", help="Derive domain from work email"),
        employer: Optional[str] = typer.Option(None, help="Use if employer string is a hostname"),
        subject: Optional[str] = typer.Option(
            None,
            "--subject",
            "-s",
            help="Link results to an existing subject dossier",
        ),
        output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
        no_tls: bool = typer.Option(False, "--no-tls", help="Skip tlsx certificate scan"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running"),
        create: bool = typer.Option(False, "--create", help="Create subject if missing (requires --subject)"),
    ) -> None:
        """Enumerate subdomains and probe live hosts for a business or owned domain."""
        debug = get_debug(ctx)
        resolved = resolve_scan_domain(domain=domain, email=email, employer=employer)
        if not resolved:
            console.print(
                "[red]No scannable domain.[/] Pass a domain, or use a non-free email "
                "(not gmail/yahoo/outlook)."
            )
            raise typer.Exit(1)

        console.print(f"[bold]Domain recon[/] → {resolved}")
        out_dir = output or Path("out") / "domain" / resolved.replace(".", "_")
        recon = run_domain_recon(
            domain=resolved,
            output_dir=out_dir,
            include_tls=not no_tls,
            dry_run=dry_run,
        )

        if dry_run:
            console.print(f"[dim]Output dir:[/] {out_dir.resolve()}")
            console.print("[green]Dry run complete.[/]")
            raise typer.Exit(0)

        if recon.errors:
            for err in recon.errors:
                console.print(f"[yellow]Warning:[/] {err}")

        table = Table(title=f"Results — {resolved}")
        table.add_column("Metric")
        table.add_column("Count")
        table.add_row("Subdomains", str(len(recon.subdomains)))
        table.add_row("Live hosts", str(len(recon.live_hosts)))
        table.add_row("TLS names", str(len(recon.tls_names)))
        table.add_row("Tools run", str(recon.tools_run))
        console.print(table)

        if recon.live_hosts:
            console.print("\n[bold]Live hosts[/]")
            for row in recon.live_hosts[:15]:
                title = f" — {row['title']}" if row.get("title") else ""
                console.print(f"  {row['url']}{title}")
            if len(recon.live_hosts) > 15:
                console.print(f"  [dim]… and {len(recon.live_hosts) - 15} more[/]")

        console.print(f"\n[dim]Artifacts:[/] {out_dir.resolve()}")

        if subject:
            with SessionLocal() as session:
                try:
                    defendant = get_defendant(session, subject)
                except typer.BadParameter:
                    if not create:
                        console.print(f"[red]No subject {subject!r}.[/] Use --create to add one.")
                        raise typer.Exit(1) from None
                    defendant = ensure_subject(
                        session,
                        PipelineConfig(subject=subject, email=email, employer=employer),
                    )

                added = 0
                for row in recon.live_hosts:
                    note = f"Domain recon — {row.get('title') or ''} (status {row.get('status')})".strip()
                    if add_evidence_url(session, defendant.id, "domain-recon/httpx", row["url"], notes=note):
                        added += 1
                for host in recon.subdomains:
                    url = f"https://{host}"
                    if add_evidence_url(session, defendant.id, "domain-recon/subdomain", url, notes=f"Subdomain of {resolved}"):
                        added += 1
                leads = persist_leads(session, defendant.id, recon.lead_map, "domain-recon")
                console.print(f"[green]Linked to {subject}:[/] {added} evidence, {leads} URL leads")

        if not recon.tools_run and debug:
            raise RuntimeError("No domain recon tools completed — check FOSS_DOCKER or install PD tools.")
        if not recon.tools_run:
            console.print("[yellow]No tools completed.[/] Set FOSS_DOCKER=1 and rebuild the foss image.")
            raise typer.Exit(1)

    @domain_app.command("resolve")
    def domain_resolve(
        domain: Optional[str] = typer.Argument(None),
        email: Optional[str] = typer.Option(None, "--email", "-e"),
        employer: Optional[str] = typer.Option(None),
    ) -> None:
        """Show which domain would be scanned from the given seeds."""
        resolved = resolve_scan_domain(domain=domain, email=email, employer=employer)
        if resolved:
            console.print(resolved)
        else:
            console.print("[yellow]No scannable domain from inputs.[/]")
            raise typer.Exit(1)
