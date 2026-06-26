from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CollectResult:
    collector: str
    subject: str
    url: str
    screenshot_path: Path | None = None
    sha256: str | None = None
    notes: str = ""
    manual_steps: tuple[str, ...] = ()
    extra_urls: tuple[str, ...] = field(default_factory=tuple)


class Collector(Protocol):
    name: str
    label: str

    def collect(
        self,
        subject: str,
        *,
        capture: bool = True,
        wait_ms: int = 2000,
        state: str | None = None,
        city: str | None = None,
    ) -> CollectResult: ...


def capture_page(url: str, label: str, wait_ms: int = 2000) -> tuple[Path, str]:
    from service_osint.capture import screenshot_url

    return screenshot_url(url, label, wait_ms=wait_ms)
