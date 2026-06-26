from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from service_osint.discovery import discover, list_providers
from service_osint.cli._helpers import console


def register(discover_app: typer.Typer) -> None:
    @discover_app.command("providers")
    def discover_providers() -> None:
        """Show which discovery backends are configured."""
        t = Table(title="Discovery Providers")
        t.add_column("Provider")
        t.add_column("Ready")
        t.add_column("Notes")
        for name, ready, notes in list_providers():
            t.add_row(name, "[green]yes[/]" if ready else "[dim]no[/]", notes)
        console.print(t)

    @discover_app.command("search")
    def discover_search(
        query: str,
        limit: int = typer.Option(8, min=1, max=20),
        provider: Optional[str] = typer.Option(
            None, help="searxng|serper|tavily|exa|brave|linkup|firecrawl|duckduckgo"
        ),
    ) -> None:
        """Run tiered web discovery across configured providers."""
        results = discover(query, limit=limit, provider=provider)
        for block in results:
            console.print(f"\n[bold cyan]{block.provider}[/] — {block.query}")
            if block.error:
                console.print(f"[yellow]{block.error}[/]")
                continue
            if not block.hits:
                console.print("[dim]No hits.[/]")
                continue
            t = Table()
            t.add_column("#")
            t.add_column("Title")
            t.add_column("URL")
            t.add_column("Snippet")
            for hit in block.hits:
                t.add_row(str(hit.rank), hit.title[:60], hit.url[:70], (hit.snippet or "")[:120])
            console.print(t)

    @discover_app.command("person")
    def discover_person(
        name: str,
        city: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = typer.Option(8, min=1, max=20),
        provider: Optional[str] = None,
    ) -> None:
        """Discovery search tuned for an individual skip-trace lead."""
        parts = [f'"{name}"']
        if city:
            parts.append(city)
        if state:
            parts.append(state)
        parts.append("(address OR phone OR residence OR contact)")
        discover_search(" ".join(parts), limit=limit, provider=provider)
