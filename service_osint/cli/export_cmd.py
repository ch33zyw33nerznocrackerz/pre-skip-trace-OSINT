from __future__ import annotations

from pathlib import Path
import typer

from service_osint.core.db import SessionLocal
from service_osint.export import write_addresses_csv, write_html_packet, write_json, write_pdf_packet
from service_osint.cli._helpers import console, get_defendant


def register(export_app: typer.Typer) -> None:
    @export_app.command("csv")
    def export_csv(name: str, out: Path) -> None:
        with SessionLocal() as s:
            write_addresses_csv(get_defendant(s, name), out)
            console.print(f"[green]Exported CSV:[/] {out}")

    @export_app.command("json")
    def export_json(name: str, out: Path) -> None:
        with SessionLocal() as s:
            write_json(get_defendant(s, name), out)
            console.print(f"[green]Exported JSON:[/] {out}")

    @export_app.command("html")
    def export_html(name: str, out: Path) -> None:
        with SessionLocal() as s:
            write_html_packet(get_defendant(s, name), out)
            console.print(f"[green]Exported HTML packet:[/] {out}")

    @export_app.command("pdf")
    def export_pdf(name: str, out: Path) -> None:
        with SessionLocal() as s:
            write_pdf_packet(get_defendant(s, name), out)
            console.print(f"[green]Exported PDF packet:[/] {out}")
