from __future__ import annotations

import typer

from service_osint.core.config import get_config
from service_osint.core.db import init_db
from service_osint.core.env import load_env
from service_osint.core.logging import setup_logging
from service_osint.cli import (
    collect_cmd,
    discovery_cmd,
    domain_cmd,
    dorks_cmd,
    export_cmd,
    foss_cmd,
    health_cmd,
    packet_cmd,
    run_cmd,
    seeds,
    social_cmd,
    sources_cmd,
    subjects,
)
from service_osint.core.errors import DatabaseError

app = typer.Typer(
    help="Lawful skip-trace OSINT for process servers. Run [bold]osint[/] alone for interactive mode.",
    invoke_without_command=True,
)
sources_app = typer.Typer(help="Public-record and people-search bookmarks")
export_app = typer.Typer(help="Export packets")
discover_app = typer.Typer(help="Tiered web discovery (SearXNG, Serper, Brave, Linkup, Firecrawl)")
dorks_app = typer.Typer(help="Google dork seed queries for individual skip-trace")
collect_app = typer.Typer(help="Public-record collectors (SEC, NV SOS, property, socials)")

app.add_typer(sources_app, name="sources")
app.add_typer(export_app, name="export")
app.add_typer(discover_app, name="discover")
app.add_typer(dorks_app, name="dorks")
app.add_typer(collect_app, name="collect")

subjects.register(app)
sources_cmd.register(sources_app)
discovery_cmd.register(discover_app)
dorks_cmd.register(dorks_app)
export_cmd.register(export_app)
collect_cmd.register(collect_app)
domain_cmd.register(app)
packet_cmd.register(app)
run_cmd.register(app)
foss_cmd.register(app)
social_cmd.register(app)
health_cmd.register(app)
seeds.register(app, sources_app)


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", "-d", help="Verbose error output"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    log_json: bool = typer.Option(False, "--log-json", help="JSON log format"),
) -> None:
    """Initialize DB; launch interactive wizard when no subcommand is given."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    
    # Load environment and configuration
    load_env()
    config = get_config()
    
    # Override config with CLI options
    if debug:
        config.debug = True
        config.log_level = "DEBUG"
    if log_level != "INFO":
        config.log_level = log_level.upper()
        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if config.log_level not in valid_levels:
            import typer as _typer
            _typer.echo(f"Invalid log level: {log_level}. Must be one of: {', '.join(valid_levels)}", err=True)
            raise _typer.Exit(1)
    if log_json:
        config.log_json = True
    
    # Setup logging
    setup_logging(
        level=config.log_level,
        log_file=True,
        json_format=config.log_json,
    )
    
    try:
        init_db()
    except DatabaseError as exc:
        import typer as _typer

        _typer.echo(f"Database initialization failed: {exc}", err=True)
        if exc.hint:
            _typer.echo(f"Hint: {exc.hint}", err=True)
        if debug:
            raise
        raise _typer.Exit(1) from exc
    
    if ctx.invoked_subcommand is None:
        from service_osint.cli.interactive import run_interactive_wizard

        run_interactive_wizard()
        raise typer.Exit()
