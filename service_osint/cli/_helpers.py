from __future__ import annotations

import typer
from rich.console import Console
from sqlalchemy import select

from service_osint.core.errors import format_osint_error
from service_osint.core.models import Defendant

console = Console()


def get_debug(ctx: typer.Context | None) -> bool:
    """Return True when the global --debug flag was passed."""
    if not ctx or not ctx.obj:
        return False
    return bool(ctx.obj.get("debug"))


def exit_on_osint_error(exc: BaseException, *, debug: bool = False) -> None:
    """Print a friendly message and exit; re-raise when debug is enabled."""
    if debug:
        raise exc
    message, hint = format_osint_error(exc)
    console.print(f"[red]Error:[/] {message}")
    if hint:
        console.print(f"[dim]{hint}[/]")
    raise typer.Exit(1) from exc


def get_defendant(session, name: str) -> Defendant:
    obj = session.scalar(select(Defendant).where(Defendant.name == name))
    if not obj:
        raise typer.BadParameter(f"No subject named {name!r}. Add first with add-subject.")
    return obj
