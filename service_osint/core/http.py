from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator

import httpx

from service_osint.core.api_keys import RateLimiter
from service_osint.core.config import get_config

logger = logging.getLogger(__name__)


class HttpClient:
    """Shared HTTP client with connection pooling and rate limiting."""
    
    def __init__(self) -> None:
        self.config = get_config()
        self.rate_limiter = RateLimiter(self.config.default_rate_limit)
        self._client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None
    
    @property
    def client(self) -> httpx.Client:
        """Get or create synchronous HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.config.request_timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=self.config.max_concurrent_requests,
                    max_connections=self.config.max_concurrent_requests * 2,
                ),
                follow_redirects=True,
            )
        return self._client
    
    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                timeout=self.config.request_timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=self.config.max_concurrent_requests,
                    max_connections=self.config.max_concurrent_requests * 2,
                ),
                follow_redirects=True,
            )
        return self._async_client
    
    def request(
        self,
        method: str,
        url: str,
        *,
        rate_limit: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with rate limiting."""
        if rate_limit:
            self.rate_limiter.wait_if_needed()
        
        logger.debug(f"HTTP {method.upper()} {url}")
        response = self.client.request(method, url, **kwargs)
        logger.debug(f"HTTP {response.status_code} {url}")
        return response
    
    async def async_request(
        self,
        method: str,
        url: str,
        *,
        rate_limit: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async HTTP request with rate limiting."""
        if rate_limit:
            # Convert sync rate limiter to async
            await asyncio.to_thread(self.rate_limiter.wait_if_needed)
        
        logger.debug(f"HTTP {method.upper()} {url}")
        response = await self.async_client.request(method, url, **kwargs)
        logger.debug(f"HTTP {response.status_code} {url}")
        return response
    
    def close(self) -> None:
        """Close HTTP clients."""
        if self._client:
            self._client.close()
            self._client = None
        if self._async_client:
            asyncio.create_task(self._async_client.aclose())
            self._async_client = None


# Global HTTP client instance
_http_client: HttpClient | None = None


def get_http_client() -> HttpClient:
    """Get the global HTTP client instance."""
    global _http_client
    if _http_client is None:
        _http_client = HttpClient()
    return _http_client


@contextmanager
def http_client() -> Generator[HttpClient, None, None]:
    """Context manager for HTTP client."""
    client = get_http_client()
    try:
        yield client
    finally:
        pass  # Keep client alive for reuse


@asynccontextmanager
async def async_http_client() -> AsyncGenerator[HttpClient, None]:
    """Async context manager for HTTP client."""
    client = get_http_client()
    try:
        yield client
    finally:
        pass  # Keep client alive for reuse
