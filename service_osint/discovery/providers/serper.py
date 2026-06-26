from __future__ import annotations

import httpx

from service_osint.core.errors import provider_error_message

from ..base import DiscoveryResult, SearchHit
from ..config import DiscoveryConfig


class SerperProvider:
    name = "serper"

    def __init__(self, config: DiscoveryConfig) -> None:
        self._key = config.serper_api_key

    def available(self) -> bool:
        return bool(self._key)

    def search(self, query: str, *, limit: int = 10) -> DiscoveryResult:
        if not self.available():
            return DiscoveryResult(query=query, provider=self.name, error="SERPER_API_KEY not set")
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self._key or "", "Content-Type": "application/json"},
                    json={"q": query, "num": limit},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return DiscoveryResult(
                query=query, provider=self.name, error=provider_error_message(self.name, exc)
            )
        organic = data.get("organic") or []
        hits = [
            SearchHit(
                title=str(r.get("title") or ""),
                url=str(r.get("link") or ""),
                snippet=str(r.get("snippet") or ""),
                provider=self.name,
                rank=i + 1,
            )
            for i, r in enumerate(organic[:limit])
        ]
        return DiscoveryResult(query=query, provider=self.name, hits=hits, raw_count=len(organic))
