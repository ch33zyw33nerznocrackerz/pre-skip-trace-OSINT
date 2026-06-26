from __future__ import annotations

import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import httpx

# Health check constants
DEFAULT_SEARXNG_TIMEOUT = 15.0
DEFAULT_SEARXNG_RETRIES = 4
SEARXNG_RETRY_DELAY = 3.0
from sqlalchemy import inspect, text

from service_osint.core.db import APP_DIR, DB_PATH, SessionLocal, engine, init_db
from service_osint.core.env import env_summary, find_env_file
from service_osint.core.errors import DatabaseError, format_http_error
from service_osint.discovery.config import DiscoveryConfig
from service_osint.discovery.router import list_providers

HealthStatus = Literal["ok", "warn", "fail"]

REQUIRED_TABLES = frozenset(
    {"defendants", "addresses", "evidence", "leads", "service_attempts"}
)


@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    hint: str = ""
    duration_ms: float = 0.0
    details: dict[str, str] = field(default_factory=dict)


def _timed(fn) -> HealthCheck:
    start = time.perf_counter()
    result = fn()
    result.duration_ms = round((time.perf_counter() - start) * 1000, 1)
    return result


def check_python() -> HealthCheck:
    import sys

    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 12)
    return HealthCheck(
        name="python",
        status="ok" if ok else "fail",
        message=f"Python {version}",
        hint="" if ok else "Requires Python 3.12+ (see pyproject.toml).",
    )


def check_app_directories() -> HealthCheck:
    captures = APP_DIR / "captures"
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        captures.mkdir(parents=True, exist_ok=True)
        probe = APP_DIR / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        return HealthCheck(
            name="app_dirs",
            status="fail",
            message=str(exc),
            hint=f"Ensure {APP_DIR} is writable.",
        )
    return HealthCheck(
        name="app_dirs",
        status="ok",
        message=f"Data dir: {APP_DIR}",
        details={"db": str(DB_PATH), "captures": str(captures)},
    )


def check_database(*, create: bool = False) -> HealthCheck:
    try:
        if create:
            init_db()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        tables = set(inspect(engine).get_table_names())
        if not tables:
            return HealthCheck(
                name="database",
                status="warn",
                message="Connected but no tables found",
                hint="Run any osint command to initialize schema, or `osint health --init`.",
            )
        missing = REQUIRED_TABLES - tables
        if missing:
            return HealthCheck(
                name="database",
                status="warn",
                message=f"Schema incomplete — missing: {', '.join(sorted(missing))}",
                hint="Run `osint health --init` to recreate tables.",
                details={"path": str(DB_PATH), "tables": str(len(tables))},
            )
        with SessionLocal() as session:
            session.execute(text("SELECT COUNT(*) FROM defendants"))
        return HealthCheck(
            name="database",
            status="ok",
            message=f"SQLite OK ({len(tables)} tables)",
            details={"path": str(DB_PATH)},
        )
    except DatabaseError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(str(exc), hint="Check permissions on ~/.service-osint/case.db") from exc


def check_database_safe(*, create: bool = False) -> HealthCheck:
    try:
        return check_database(create=create)
    except DatabaseError as exc:
        return HealthCheck(
            name="database",
            status="fail",
            message=str(exc),
            hint=exc.hint,
        )
    except Exception as exc:  # noqa: BLE001
        return HealthCheck(name="database", status="fail", message=str(exc))


def check_env_file() -> HealthCheck:
    path = find_env_file()
    if path:
        return HealthCheck(
            name="env_file",
            status="ok",
            message=f"Loaded from {path}",
        )
    return HealthCheck(
        name="env_file",
        status="warn",
        message="No .env file found",
        hint="Copy .env.example to .env and add API keys.",
    )


def check_discovery_providers() -> HealthCheck:
    rows = list_providers()
    ready = [name for name, ok, _ in rows if ok]
    if not ready:
        return HealthCheck(
            name="discovery",
            status="fail",
            message="No discovery providers configured",
            hint="Set SEARXNG_URL or an API key — see `osint discover providers`.",
            details={name: "ready" if ok else "missing" for name, ok, _ in rows},
        )
    if len(ready) == 1 and ready == ["duckduckgo"]:
        return HealthCheck(
            name="discovery",
            status="warn",
            message="Only DuckDuckGo fallback is available",
            hint="Add SEARXNG_URL or SERPER_API_KEY for better results.",
            details={name: "ready" if ok else "missing" for name, ok, _ in rows},
        )
    return HealthCheck(
        name="discovery",
        status="ok",
        message=f"{len(ready)} provider(s) ready: {', '.join(ready)}",
        details={name: "ready" if ok else "missing" for name, ok, _ in rows},
    )


def check_searxng(*, timeout: float = DEFAULT_SEARXNG_TIMEOUT, retries: int = DEFAULT_SEARXNG_RETRIES) -> HealthCheck:
    cfg = DiscoveryConfig.from_env()
    base = (cfg.searxng_url or "").rstrip("/")
    if not base:
        return HealthCheck(
            name="searxng",
            status="warn",
            message="SEARXNG_URL not set",
            hint="docker compose -f docker/docker-compose.yml up -d",
        )

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                healthz = client.get(f"{base}/healthz")
                if healthz.status_code < 500:
                    # Optional search probe — engines may be slow; healthz is enough for "up"
                    try:
                        resp = client.get(
                            f"{base}/search",
                            params={"q": "healthcheck", "format": "json"},
                            headers={"User-Agent": "service-osint-health/1.0"},
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        count = len(data.get("results") or [])
                        return HealthCheck(
                            name="searxng",
                            status="ok",
                            message=f"Reachable at {base} ({count} test hits)",
                        )
                    except Exception as search_exc:  # noqa: BLE001
                        return HealthCheck(
                            name="searxng",
                            status="warn",
                            message=f"Up at {base} (healthz ok; search probe: {search_exc})",
                            hint="SearXNG is running — discovery may still work. Try `just searxng-reset` if searches fail.",
                        )
                raise httpx.HTTPStatusError(
                    f"healthz {healthz.status_code}",
                    request=healthz.request,
                    response=healthz,
                )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(SEARXNG_RETRY_DELAY)
                continue

    assert last_exc is not None
    hint = "Run `just searxng-reset` then `just doctor`."
    if shutil.which("docker"):
        hint = f"{hint} Or: just docker-searxng"
    return HealthCheck(
        name="searxng",
        status="fail",
        message=format_http_error(last_exc, context="SearXNG"),
        hint=hint,
    )


def check_docker() -> HealthCheck:
    if not shutil.which("docker"):
        return HealthCheck(
            name="docker",
            status="warn",
            message="docker not in PATH",
            hint="Install Docker Desktop or unset FOSS_DOCKER for local tool installs.",
        )
    compose_raw = os.getenv("DOCKER_COMPOSE_FILE", "docker/docker-compose.yml")
    compose = Path(compose_raw)
    if not compose.is_absolute():
        compose = Path.cwd() / compose
    if not compose.is_file():
        return HealthCheck(
            name="docker",
            status="warn",
            message=f"Compose file missing: {compose}",
            hint="Set DOCKER_COMPOSE_FILE or run from project root.",
        )
    return HealthCheck(
        name="docker",
        status="ok",
        message="docker available",
        details={"compose": str(compose.resolve())},
    )


def check_foss_tools() -> HealthCheck:
    from service_osint.foss.integrations import check_tool_available, list_foss_tools, use_docker_foss

    tools = list_foss_tools()
    ready = []
    missing: list[str] = []
    for tool in tools:
        ok, _ = check_tool_available(tool)
        (ready if ok else missing).append(tool.id)

    mode = "docker" if use_docker_foss() else "local"
    if not ready:
        return HealthCheck(
            name="foss",
            status="warn",
            message=f"No FOSS tools ready ({mode} mode)",
            hint="Run `osint foss install-guide` or enable FOSS_DOCKER=1.",
            details={t: "ready" if t in ready else "missing" for t in [x.id for x in tools]},
        )
    return HealthCheck(
        name="foss",
        status="ok" if len(ready) == len(tools) else "warn",
        message=f"{len(ready)}/{len(tools)} tools ready ({mode})",
        details={t.id: "ready" if t.id in ready else "missing" for t in tools},
    )


def _playwright_browser_dir() -> Path | None:
    """Return the Playwright browser cache directory for the current OS."""
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA")
        return Path(local) / "ms-playwright" if local else Path.home() / "AppData" / "Local" / "ms-playwright"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "ms-playwright"


def check_playwright() -> HealthCheck:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return HealthCheck(
            name="playwright",
            status="fail",
            message="playwright package not installed",
            hint="uv sync && uv run playwright install chromium",
        )
    browser_dir = _playwright_browser_dir()
    if browser_dir and browser_dir.is_dir() and any(browser_dir.iterdir()):
        return HealthCheck(
            name="playwright",
            status="ok",
            message="Playwright + browser cache found",
            details={"cache": str(browser_dir)},
        )
    return HealthCheck(
        name="playwright",
        status="warn",
        message="Playwright installed but browsers may be missing",
        hint="uv run playwright install chromium",
    )


def run_health_checks(
    *,
    init_db_if_missing: bool = False,
    probe_searxng: bool = False,
    include_foss: bool = True,
    include_playwright: bool = False,
) -> list[HealthCheck]:
    """Run all startup health checks."""
    checks: list[HealthCheck] = [
        _timed(check_python),
        _timed(check_app_directories),
        _timed(check_env_file),
        _timed(lambda: check_database_safe(create=init_db_if_missing)),
        _timed(check_discovery_providers),
    ]
    if probe_searxng:
        checks.append(_timed(check_searxng))
    checks.append(_timed(check_docker))
    if include_foss:
        checks.append(_timed(check_foss_tools))
    if include_playwright:
        checks.append(_timed(check_playwright))
    return checks


def overall_status(checks: list[HealthCheck]) -> HealthStatus:
    if any(c.status == "fail" for c in checks):
        return "fail"
    if any(c.status == "warn" for c in checks):
        return "warn"
    return "ok"


def env_keys_summary() -> HealthCheck:
    summary = env_summary()
    configured = [k for k, v in summary.items() if v == "(set)"]
    return HealthCheck(
        name="api_keys",
        status="ok" if configured else "warn",
        message=f"{len(configured)} env var(s) configured",
        details=summary,
    )


def health_checks_to_dict(checks: list[HealthCheck]) -> dict[str, Any]:
    """Serialize health checks for --json output and scripting."""
    return {
        "status": overall_status(checks),
        "checks": [
            {
                "name": c.name,
                "status": c.status,
                "message": c.message,
                "hint": c.hint,
                "duration_ms": c.duration_ms,
                "details": c.details,
            }
            for c in checks
        ],
    }
