from __future__ import annotations

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, TypeVar

from service_osint.core.config import get_config

T = TypeVar("T")


class FileCache:
    """Simple file-based cache with TTL support."""
    
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.config = get_config()
        self.cache_dir = cache_dir or self.config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _cache_key(self, key: str) -> str:
        """Generate cache key hash."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _cache_path(self, key: str) -> Path:
        """Get cache file path."""
        cache_key = self._cache_key(key)
        return self.cache_dir / f"{cache_key}.cache"
    
    def get(self, key: str, default: T | None = None) -> T | None:
        """Get value from cache."""
        cache_path = self._cache_path(key)
        
        if not cache_path.exists():
            return default
        
        try:
            with cache_path.open("rb") as f:
                data = pickle.load(f)
            
            # Check TTL
            if time.time() - data["timestamp"] > self.config.cache_ttl:
                cache_path.unlink(missing_ok=True)
                return default
            
            return data["value"]
        except Exception:
            # Corrupted cache file
            cache_path.unlink(missing_ok=True)
            return default
    
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        cache_path = self._cache_path(key)
        
        data = {
            "timestamp": time.time(),
            "ttl": ttl or self.config.cache_ttl,
            "value": value,
        }
        
        try:
            with cache_path.open("wb") as f:
                pickle.dump(data, f)
        except Exception:
            # Ignore cache write failures
            pass
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        cache_path = self._cache_path(key)
        cache_path.unlink(missing_ok=True)
    
    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink(missing_ok=True)
    
    def cleanup(self) -> int:
        """Remove expired cache files. Returns number of files removed."""
        removed = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with cache_file.open("rb") as f:
                    data = pickle.load(f)
                
                if current_time - data["timestamp"] > data.get("ttl", self.config.cache_ttl):
                    cache_file.unlink()
                    removed += 1
            except Exception:
                # Corrupted file, remove it
                cache_file.unlink(missing_ok=True)
                removed += 1
        
        return removed


# Global cache instance
_cache: FileCache | None = None


def get_cache() -> FileCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = FileCache()
    return _cache


def cached(key_prefix: str = "", ttl: int | None = None):
    """Decorator for caching function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            if args:
                key_parts.append(str(hash(args)))
            if kwargs:
                key_parts.append(str(hash(tuple(sorted(kwargs.items())))))
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
