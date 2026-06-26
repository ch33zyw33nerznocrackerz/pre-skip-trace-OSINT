from __future__ import annotations

import httpx

from service_osint.core.errors import provider_error_message

from ..base import DiscoveryResult, SearchHit
from ..config import DiscoveryConfig


class BraveProvider:
    name = "brave"

    def __init__(self, config: DiscoveryConfig) -> None:
        self._key = config.brave_api_key

    def available(self) -> bool:
        return bool(self._key)

    def search(self, query: str, *, limit: int = 10) -> DiscoveryResult:
        if not self.available():
            return DiscoveryResult(query=query, provider=self.name, error="BRAVE_API_KEY not set")
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={"Accept": "application/json", "X-Subscription-Token": self._key or ""},
                    params={"q": query, "count": limit},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return DiscoveryResult(
                query=query, provider=self.name, error=provider_error_message(self.name, exc)
            )
        web = (data.get("web") or {}).get("results") or []
        hits = [
            SearchHit(
                title=str(r.get("title") or ""),
                url=str(r.get("url") or ""),
                snippet=str(r.get("description") or ""),
                provider=self.name,
                rank=i + 1,
            )
            for i, r in enumerate(web[:limit])
        ]
        return DiscoveryResult(query=query, provider=self.name, hits=hits, raw_count=len(web))
