"""Recreate SearXNG container and wipe its cache volume."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", "docker/docker-compose.yml"]


def _wait_and_doctor() -> int:
    script = ROOT / "scripts" / "wait_searxng.py"
    result = subprocess.run(
        ["uv", "run", "python", str(script), "--doctor"],
        cwd=ROOT,
        check=False,
    )
    return int(result.returncode or 0)


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True)


def main() -> None:
    run([*COMPOSE, "stop", "searxng"], check=False)
    run([*COMPOSE, "rm", "-f", "searxng"], check=False)
    listed = subprocess.run(
        ["docker", "volume", "ls", "-q", "--filter", "name=searxng-cache"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    for vol in listed.stdout.splitlines():
        vol = vol.strip()
        if vol:
            run(["docker", "volume", "rm", "-f", vol], check=False)
    run([*COMPOSE, "pull", "searxng"], check=False)
    run([*COMPOSE, "up", "-d", "searxng"])
    code = _wait_and_doctor()
    raise SystemExit(code)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
