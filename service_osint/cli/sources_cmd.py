from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table
from sqlalchemy import select

from service_osint.core.db import SessionLocal
from service_osint.core.models import SourceBookmark
from service_osint.sources import DEFAULT_SOURCES
from service_osint.cli._helpers import console


def seed_bookmarks() -> int:
    with SessionLocal() as s:
        count = 0
        for name, cat, juris, url, notes in DEFAULT_SOURCES:
            exists = s.scalar(select(SourceBookmark).where(SourceBookmark.name == name, SourceBookmark.url == url))
            if not exists:
                s.add(SourceBookmark(name=name, category=cat, jurisdiction=juris, url=url, notes=notes))
                count += 1
        s.commit()
        return count


def register(sources_app: typer.Typer) -> None:
    @sources_app.command("seed")
    def sources_seed() -> None:
        count = seed_bookmarks()
        console.print(f"[green]Seeded {count} source bookmarks.[/]")

    @sources_app.command("list")
    def sources_list(category: Optional[str] = None, jurisdiction: Optional[str] = None) -> None:
        with SessionLocal() as s:
            q = select(SourceBookmark)
            if category:
                q = q.where(SourceBookmark.category == category)
            if jurisdiction:
                q = q.where(SourceBookmark.jurisdiction == jurisdiction)
            rows = s.scalars(q.order_by(SourceBookmark.jurisdiction, SourceBookmark.category, SourceBookmark.name)).all()
            t = Table(title="Source Bookmarks")
            for c in ["ID", "Jurisdiction", "Category", "Name", "URL", "Notes"]:
                t.add_column(c)
            for r in rows:
                t.add_row(str(r.id), r.jurisdiction or "", r.category, r.name, r.url, r.notes or "")
            console.print(t)
