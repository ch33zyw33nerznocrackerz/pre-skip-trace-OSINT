from __future__ import annotations

import typer
from sqlalchemy import select

from service_osint.core.db import SessionLocal
from service_osint.core.models import Defendant
from service_osint.cli._helpers import console
from service_osint.cli.sources_cmd import seed_bookmarks


def register(app: typer.Typer, sources_app: typer.Typer) -> None:
    @app.command("seed-person")
    def seed_person() -> None:
        """Seed individual skip-trace bookmarks + example subject placeholders."""
        with SessionLocal() as s:
            if not s.scalar(select(Defendant).where(Defendant.name == "Example Person")):
                s.add(
                    Defendant(
                        name="Example Person",
                        role="Individual defendant",
                        entity_type="person",
                        notes="Replace with real case data",
                    )
                )
                s.commit()
        count = seed_bookmarks()
        console.print(f"[green]Seeded {count} source bookmarks.[/]")
        console.print("[cyan]Seeded people-search, dork-tool, and public-record bookmarks.[/]")
        console.print('Run: osint dorks urls "Jane Doe" --city "Las Vegas" --state NV')

    @app.command("seed-aabb")
    def seed_aabb() -> None:
        """Create starter corporate case records (legacy example)."""
        for name, role, typ in [
            ("Asia Broadband, Inc.", "Corporate defendant", "company"),
            ("Chris Torres", "Officer defendant", "person"),
            ("Bernard Velez", "Officer defendant", "person"),
        ]:
            with SessionLocal() as s:
                if not s.scalar(select(Defendant).where(Defendant.name == name)):
                    s.add(Defendant(name=name, role=role, entity_type=typ))
                    s.commit()
        seed_bookmarks()
        console.print("[cyan]Seeded AABB starter subjects + source bookmarks.[/]")

    _ = sources_app  # sub-app registered elsewhere
