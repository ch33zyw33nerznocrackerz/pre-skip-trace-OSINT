from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


@dataclass
class FossTool:
    id: str
    name: str
    repo: str
    install: str
    command: list[str]
    input: str
    category: str
    description: str
    cwd_env: str | None = None
    docker_cwd: str | None = None
    runner: str = "auto"  # auto | python | binary
    timeout_seconds: int = 600


@dataclass
class FossTarget:
    name: str | None = None
    email: str | None = None
    domain: str | None = None
    url: str | None = None
    username: str | None = None
    phone: str | None = None
    usernames: list[str] = field(default_factory=list)

    @property
    def resolved_domain(self) -> str | None:
        if self.domain:
            return self.domain.strip().lower().removeprefix("www.")
        if self.email and "@" in self.email:
            return self.email.split("@", 1)[1].strip().lower()
        return None


def load_foss_tools() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for filename in ("foss_tools.yaml", "foss_tools_social.yaml", "foss_tools_domain.yaml"):
        path = CONFIG_DIR / filename
        if not path.is_file():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tools.extend(data.get("tools") or [])
    return tools

