from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from service_osint.core.db import APP_DIR


@dataclass
class AppConfig:
    """Application-wide configuration."""
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = False
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    cache_ttl: int = 3600
    screenshot_timeout: int = 30000
    screenshot_wait: int = 2000
    
    # Database settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    
    # Rate limiting
    default_rate_limit: int = 60  # requests per minute
    discovery_rate_limit: int = 30
    collector_rate_limit: int = 20
    
    # File paths
    config_dir: Path = field(default_factory=lambda: APP_DIR)
    cache_dir: Path = field(default_factory=lambda: APP_DIR / "cache")
    temp_dir: Path = field(default_factory=lambda: APP_DIR / "temp")
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        return cls(
            debug=os.getenv("OSINT_DEBUG", "false").lower() == "true",
            log_level=os.getenv("OSINT_LOG_LEVEL", "INFO").upper(),
            log_json=os.getenv("OSINT_LOG_JSON", "false").lower() == "true",
            max_concurrent_requests=int(os.getenv("OSINT_MAX_CONCURRENT", "10")),
            request_timeout=float(os.getenv("OSINT_REQUEST_TIMEOUT", "30.0")),
            retry_attempts=int(os.getenv("OSINT_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("OSINT_RETRY_DELAY", "1.0")),
            cache_ttl=int(os.getenv("OSINT_CACHE_TTL", "3600")),
            screenshot_timeout=int(os.getenv("OSINT_SCREENSHOT_TIMEOUT", "30000")),
            screenshot_wait=int(os.getenv("OSINT_SCREENSHOT_WAIT", "2000")),
            default_rate_limit=int(os.getenv("OSINT_RATE_LIMIT", "60")),
            discovery_rate_limit=int(os.getenv("OSINT_DISCOVERY_RATE_LIMIT", "30")),
            collector_rate_limit=int(os.getenv("OSINT_COLLECTOR_RATE_LIMIT", "20")),
        )
    
    def ensure_directories(self) -> None:
        """Create necessary directories."""
        for path in [self.config_dir, self.cache_dir, self.temp_dir]:
            path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
        }


# Global config instance
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global application configuration."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
        _config.ensure_directories()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment."""
    global _config
    _config = AppConfig.from_env()
    _config.ensure_directories()
    return _config
