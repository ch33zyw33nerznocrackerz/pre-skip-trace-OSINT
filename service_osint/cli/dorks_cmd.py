from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from service_osint.sources import (
    ddg_search_url,
    fastpeoplesearch_url,
    google_search_url,
    person_dorks,
    truepeoplesearch_url,
)
from service_osint.cli._helpers import console


def register(dorks_app: typer.Typer) -> None:
    @dorks_app.command("list")
    def dorks_list(
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        employer: Optional[str] = None,
    ) -> None:
        """Print Google dork seed queries for manual search."""
        t = Table(title=f"Dork seeds — {name}")
        t.add_column("Label")
        t.add_column("Query")
        t.add_column("Purpose")
        for d in person_dorks(name, city=city, state=state, phone=phone, email=email, employer=employer):
            t.add_row(d.label, d.query, d.purpose)
        console.print(t)

    @dorks_app.command("urls")
    def dorks_urls(
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
    ) -> None:
        """Print ready-to-open search URLs (Google, DuckDuckGo, people finders)."""
        console.print("[bold]People finder deep links[/]")
        console.print(f"  TruePeopleSearch: {truepeoplesearch_url(name, city, state)}")
        console.print(f"  FastPeopleSearch: {fastpeoplesearch_url(name, city, state)}")
        console.print("\n[bold]Top dork searches (Google)[/]")
        for d in person_dorks(name, city=city, state=state)[:6]:
            console.print(f"  {d.label}: {google_search_url(d.query)}")
        console.print("\n[bold]Same dorks (DuckDuckGo)[/]")
        for d in person_dorks(name, city=city, state=state)[:3]:
            console.print(f"  {d.label}: {ddg_search_url(d.query)}")
