from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str
    provider: str
    rank: int = 0


@dataclass
class DiscoveryResult:
    query: str
    provider: str
    hits: list[SearchHit] = field(default_factory=list)
    error: str | None = None
    raw_count: int = 0


class SearchProvider(Protocol):
    name: str

    def available(self) -> bool: ...

    def search(self, query: str, *, limit: int = 10) -> DiscoveryResult: ...
