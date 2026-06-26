from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from service_osint.foss import (
    FossTarget,
    check_tool_available,
    export_install_guide,
    get_foss_tool,
    list_foss_tools,
    run_foss_tool,
    use_docker_foss,
)
from service_osint.cli._helpers import console


def register(app: typer.Typer) -> None:
    foss_app = typer.Typer(help="FOSS tools: SpiderFoot, Photon (local or Docker)")
    app.add_typer(foss_app, name="foss")

    @foss_app.command("list")
    def foss_list() -> None:
        """Show configured FOSS tools and availability."""
        mode = "docker" if use_docker_foss() else "local"
        console.print(f"[bold]FOSS tools[/] (mode: {mode})")
        for tool in list_foss_tools():
            ok, detail = check_tool_available(tool)
            style = "green" if ok else "yellow"
            console.print(f"  [{style}]{tool.id}[/] — {tool.name} ({detail})")

    @foss_app.command("install-guide")
    def foss_install_guide(
        output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write markdown guide"),
    ) -> None:
        """Print Docker + local install steps for SpiderFoot and Photon."""
        text = export_install_guide(output)
        if output:
            console.print(f"[green]Wrote[/] {output.resolve()}")
        else:
            console.print(text)

    @foss_app.command("run")
    def foss_run(
        tool_id: str,
        email: Optional[str] = typer.Option(None),
        domain: Optional[str] = typer.Option(None),
        url: Optional[str] = typer.Option(None),
        username: Optional[str] = typer.Option(None, "--username", "-u"),
        phone: Optional[str] = typer.Option(None, "--phone", "-p"),
        output: Optional[Path] = typer.Option(None, "--output", "-o"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Show command without running"),
    ) -> None:
        """Run a FOSS tool by id (spiderfoot, photon, sherlock, holehe, …)."""
        tool = get_foss_tool(tool_id)
        if not tool:
            console.print(f"[red]Unknown tool:[/] {tool_id}. Try: osint foss list")
            raise typer.Exit(1)

        target = FossTarget(email=email, domain=domain, url=url, username=username, phone=phone)
        result = run_foss_tool(tool_id, target, output_dir=output, dry_run=dry_run)
        if result.get("dry_run"):
            console.print(f"[dim]Command:[/] {' '.join(result['command'])}")
            raise typer.Exit(0)
        if not result.get("success"):
            err = result.get("error") or result.get("stderr", "")[:200]
            console.print(f"[red]Failed:[/] {err}")
            if result.get("hint"):
                console.print(f"[dim]Hint:[/] {result['hint']}")
            if result.get("install"):
                console.print(f"[dim]Install:[/] {result['install']}")
            raise typer.Exit(1)
        console.print(f"[green]OK[/] {tool_id} (exit {result.get('returncode')})")
        if result.get("output_dir"):
            console.print(f"  output: {result['output_dir']}")
