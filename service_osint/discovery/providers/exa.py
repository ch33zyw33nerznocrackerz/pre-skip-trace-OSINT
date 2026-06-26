from __future__ import annotations

import httpx

from service_osint.core.errors import provider_error_message

from ..base import DiscoveryResult, SearchHit
from ..config import DiscoveryConfig


class ExaProvider:
    name = "exa"

    def __init__(self, config: DiscoveryConfig) -> None:
        self._key = config.exa_api_key

    def available(self) -> bool:
        return bool(self._key)

    def search(self, query: str, *, limit: int = 10) -> DiscoveryResult:
        if not self.available():
            return DiscoveryResult(query=query, provider=self.name, error="EXA_API_KEY not set")
        try:
            with httpx.Client(timeout=45.0) as client:
                resp = client.post(
                    "https://api.exa.ai/search",
                    headers={
                        "x-api-key": self._key or "",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "numResults": limit,
                        "type": "auto",
                        "contents": {"text": {"maxCharacters": 500}},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return DiscoveryResult(
                query=query, provider=self.name, error=provider_error_message(self.name, exc)
            )

        results = data.get("results") or []
        hits = [
            SearchHit(
                title=str(r.get("title") or r.get("url") or ""),
                url=str(r.get("url") or ""),
                snippet=str(r.get("text") or r.get("snippet") or "")[:500],
                provider=self.name,
                rank=i + 1,
            )
            for i, r in enumerate(results[:limit])
        ]
        return DiscoveryResult(query=query, provider=self.name, hits=hits, raw_count=len(results))
