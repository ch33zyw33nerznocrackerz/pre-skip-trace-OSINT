from __future__ import annotations

import json

from rich.panel import Panel
from rich.table import Table

from service_osint.core.api_keys import (
    API_KEY_SPECS,
    configured_keys,
    keys_by_category,
    missing_keys,
)
from service_osint.cli._helpers import console


def _tier_style(tier: str) -> str:
    return {
        "free": "green",
        "freemium": "yellow",
        "paid": "red",
        "self-host": "cyan",
        "builtin": "dim",
    }.get(tier, "white")


def print_api_keys_report(*, missing_only: bool = False, json_out: bool = False) -> None:
    """Show configured and missing API keys with tier and signup URLs."""
    configured = configured_keys()
    missing = missing_keys()

    if json_out:
        payload = {
            "configured_count": len(configured),
            "missing_count": len(missing),
            "configured": [
                {
                    "env_var": s.env_var,
                    "label": s.label,
                    "tier": s.tier,
                    "category": s.category,
                    "signup_url": s.signup_url,
                }
                for s in configured
            ],
            "missing": [
                {
                    "env_var": s.env_var,
                    "label": s.label,
                    "tier": s.tier,
                    "tier_label": s.tier_label(),
                    "category": s.category,
                    "signup_url": s.signup_url,
                    "notes": s.notes,
                }
                for s in missing
            ],
        }
        console.print(json.dumps(payload, indent=2))
        return

    if not missing_only and configured:
        console.print(
            Panel(f"[green]{len(configured)}[/] of {len(API_KEY_SPECS)} optional keys set", title="API keys")
        )
        t = Table(title="Configured")
        t.add_column("Variable")
        t.add_column("Service")
        t.add_column("Tier")
        for spec in configured:
            t.add_row(spec.env_var, spec.label, f"[{_tier_style(spec.tier)}]{spec.tier_label()}[/]")
        console.print(t)
        console.print()

    if missing:
        console.print(
            Panel(
                "[yellow]Add these to .env for better discovery and collectors.[/]\n"
                "DuckDuckGo works with no keys; SearXNG is free via Docker.",
                title=f"Missing keys ({len(missing)})",
            )
        )
        grouped = keys_by_category(missing)
        category_order = ("discovery", "enrichment", "domain", "collectors")
        for category in category_order:
            specs = grouped.get(category)
            if not specs:
                continue
            t = Table(title=category.replace("_", " ").title())
            t.add_column("Env variable")
            t.add_column("Service")
            t.add_column("Tier")
            t.add_column("Get key")
            t.add_column("Notes")
            for spec in specs:
                t.add_row(
                    spec.env_var,
                    spec.label,
                    f"[{_tier_style(spec.tier)}]{spec.tier_label()}[/]",
                    spec.signup_url or "—",
                    spec.notes,
                )
            console.print(t)
            console.print()

        console.print("[bold]Priority (free first):[/]")
        for spec in missing:
            if spec.tier in {"free", "self-host", "freemium"}:
                console.print(
                    f"  [{_tier_style(spec.tier)}]{spec.tier_label()}[/] "
                    f"[cyan]{spec.env_var}[/] — {spec.signup_url}"
                )
        paid = [s for s in missing if s.tier == "paid"]
        if paid:
            console.print("\n[bold]Paid (optional):[/]")
            for spec in paid:
                console.print(f"  [red]PAID[/] [cyan]{spec.env_var}[/] — {spec.signup_url}")
    elif missing_only:
        console.print("[green]All optional API keys are set.[/]")
    else:
        console.print("[green]All optional API keys are set.[/]")

    console.print("[dim]Builtin:[/] DuckDuckGo search (no key)")
