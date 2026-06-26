from __future__ import annotations

import httpx

from service_osint.core.errors import provider_error_message

from ..base import DiscoveryResult, SearchHit
from ..config import DiscoveryConfig


class SearXNGProvider:
    name = "searxng"

    def __init__(self, config: DiscoveryConfig) -> None:
        self._base = (config.searxng_url or "").rstrip("/")

    def available(self) -> bool:
        return bool(self._base)

    def search(self, query: str, *, limit: int = 10) -> DiscoveryResult:
        if not self.available():
            return DiscoveryResult(query=query, provider=self.name, error="SEARXNG_URL not set")
        url = f"{self._base}/search"
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params={"q": query, "format": "json", "categories": "general"})
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return DiscoveryResult(
                query=query,
                provider=self.name,
                error=provider_error_message(self.name, exc),
            )
        results = data.get("results") or []
        hits = [
            SearchHit(
                title=str(r.get("title") or ""),
                url=str(r.get("url") or ""),
                snippet=str(r.get("content") or r.get("snippet") or ""),
                provider=self.name,
                rank=i + 1,
            )
            for i, r in enumerate(results[:limit])
        ]
        return DiscoveryResult(query=query, provider=self.name, hits=hits, raw_count=len(results))
