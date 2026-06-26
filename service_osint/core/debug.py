from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

from service_osint import __version__
from service_osint.core.db import APP_DIR, DB_PATH
from service_osint.core.api_keys import configured_keys, missing_keys
from service_osint.core.env import find_env_file
from service_osint.core.health import HealthCheck, overall_status, run_health_checks


@dataclass
class DebugStep:
    step: int
    title: str
    status: str
    detail: str
    action: str = ""


@dataclass
class DebugReport:
    version: str
    platform: str
    python: str
    cwd: str
    env_file: str | None
    steps: list[DebugStep] = field(default_factory=list)
    health: list[HealthCheck] = field(default_factory=list)


def collect_debug_report(
    *,
    probe_searxng: bool = True,
    init_db_if_missing: bool = True,
) -> DebugReport:
    """Gather environment + health data for `osint doctor`."""
    env_path = find_env_file()
    health = run_health_checks(
        init_db_if_missing=init_db_if_missing,
        probe_searxng=probe_searxng,
        include_foss=True,
        include_playwright=True,
    )
    steps = _build_debug_steps(health, env_path)
    return DebugReport(
        version=__version__,
        platform=platform.platform(),
        python=sys.version.split()[0],
        cwd=str(Path.cwd()),
        env_file=str(env_path) if env_path else None,
        steps=steps,
        health=health,
    )


def remediation_commands(health: list[HealthCheck]) -> list[str]:
    """Map failed/warn health checks to shell commands the user can run."""
    commands: list[str] = []
    by_name = {c.name: c for c in health}

    if by_name.get("env_file", HealthCheck("", "ok", "")).status != "ok":
        commands.append("copy .env.example .env")

    db = by_name.get("database")
    if db and db.status != "ok":
        commands.append("uv run osint health --init")

    disc = by_name.get("discovery")
    if disc and disc.status == "fail":
        commands.append("docker compose -f docker/docker-compose.yml up -d")

    searx = by_name.get("searxng")
    if searx and searx.status == "fail":
        commands.append("just searxng-reset")

    pw = by_name.get("playwright")
    if pw and pw.status != "ok":
        commands.append("uv run playwright install chromium")

    foss = by_name.get("foss")
    if foss and foss.status != "ok":
        commands.append("docker compose -f docker/docker-compose.yml --profile tools up -d foss")

    if not commands and overall_status(health) != "ok":
        commands.append("uv run osint health --probe-searxng --init")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for cmd in commands:
        if cmd not in seen:
            seen.add(cmd)
            unique.append(cmd)
    return unique


def _build_debug_steps(health: list[HealthCheck], env_path: Path | None) -> list[DebugStep]:
    steps: list[DebugStep] = []
    n = 1
    by_name = {c.name: c for c in health}

    steps.append(
        DebugStep(
            step=n,
            title="Verify install",
            status="ok",
            detail=f"service-osint {__version__} · Python {sys.version.split()[0]}",
            action="uv sync && uv run osint --help",
        )
    )
    n += 1

    if env_path:
        steps.append(
            DebugStep(
                step=n,
                title="Environment file",
                status="ok",
                detail=str(env_path),
                action="Edit .env to add API keys (see .env.example).",
            )
        )
    else:
        steps.append(
            DebugStep(
                step=n,
                title="Environment file",
                status="warn",
                detail="No .env found in cwd or project root",
                action="copy .env.example .env",
            )
        )
    n += 1

    set_keys = [s.env_var for s in configured_keys()]
    missing = missing_keys()
    free_missing = [s for s in missing if s.tier in {"free", "self-host", "freemium"}]
    detail_parts = []
    if set_keys:
        detail_parts.append(f"Set: {', '.join(set_keys)}")
    if missing:
        detail_parts.append(f"Missing {len(missing)} key(s)")
    steps.append(
        DebugStep(
            step=n,
            title="API keys",
            status="ok" if not missing else ("warn" if free_missing else "warn"),
            detail="; ".join(detail_parts) if detail_parts else "No optional keys set (DuckDuckGo still works)",
            action="Run `osint keys --missing` for tiers and signup URLs",
        )
    )
    n += 1

    steps.append(
        DebugStep(
            step=n,
            title="Data directories",
            status=by_name.get("app_dirs", HealthCheck("app_dirs", "ok", "")).status,
            detail=f"DB: {DB_PATH} · App: {APP_DIR}",
            action="Ensure ~/.service-osint is writable.",
        )
    )
    n += 1

    for check in health:
        if check.name == "app_dirs":
            continue
        steps.append(
            DebugStep(
                step=n,
                title=check.name.replace("_", " ").title(),
                status=check.status,
                detail=check.message,
                action=check.hint,
            )
        )
        n += 1

    foss_docker = os.getenv("FOSS_DOCKER", "").strip().lower() in {"1", "true", "yes"}
    if foss_docker:
        foss_check = by_name.get("foss")
        foss_status = foss_check.status if foss_check else "ok"
        steps.append(
            DebugStep(
                step=n,
                title="Docker stack",
                status=foss_status,
                detail="FOSS_DOCKER=1 — SpiderFoot/Photon run in containers",
                action="just docker-foss" if foss_status != "ok" else "",
            )
        )
    return steps
