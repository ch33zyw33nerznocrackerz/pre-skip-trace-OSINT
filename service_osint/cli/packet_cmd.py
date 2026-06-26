from __future__ import annotations

from pathlib import Path
from typing import Optional
import typer

from service_osint.core.db import SessionLocal
from service_osint.export import write_full_packet, write_pdf_packet
from service_osint.cli._helpers import console, get_defendant


def register(app: typer.Typer) -> None:
    @app.command("packet")
    def packet(
        name: str,
        out: Path = typer.Option(Path("out"), help="Output directory"),
        formats: str = typer.Option(
            "html,json,csv,pdf",
            help="Comma-separated: html,json,csv,pdf",
        ),
    ) -> None:
        """Export full service packet (HTML, JSON, CSV, PDF) for a subject."""
        fmt_set = {f.strip().lower() for f in formats.split(",") if f.strip()}
        valid = {"html", "json", "csv", "pdf"}
        bad = fmt_set - valid
        if bad:
            raise typer.BadParameter(f"Unknown formats: {', '.join(sorted(bad))}")
        with SessionLocal() as s:
            defendant = get_defendant(s, name)
            written = write_full_packet(defendant, out, formats=fmt_set)
        console.print(f"[bold]Service packet — {name}[/]")
        for kind, path in sorted(written.items()):
            console.print(f"  [green]{kind}:[/] {path.resolve()}")
        console.print("\n[dim]Review packet before service. Verify identity on every address.[/]")

    @app.command("packet-pdf")
    def packet_pdf(name: str, out: Path = typer.Option(Path("out") / "packet.pdf")) -> None:
        """Export PDF packet only (convenience alias)."""
        with SessionLocal() as s:
            write_pdf_packet(get_defendant(s, name), out)
        console.print(f"[green]PDF packet:[/] {out.resolve()}")
