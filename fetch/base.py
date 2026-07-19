"""Abstract base class for data fetchers."""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """Abstract base class for all data source fetchers."""

    def __init__(self, config: dict, cache_dir: Path):
        self.config = config
        self.cache_dir = cache_dir
        self.json_cache_dir = cache_dir / "json"
        self.readme_cache_dir = cache_dir / "readme"
        self.json_cache_dir.mkdir(parents=True, exist_ok=True)
        self.readme_cache_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch_trending(self) -> list[dict[str, Any]]:
        """Fetch trending projects."""
        ...

    @abstractmethod
    def fetch_recently_updated(self) -> list[dict[str, Any]]:
        """Fetch recently updated projects."""
        ...

    @abstractmethod
    def fetch_by_topic(self, topic: str) -> list[dict[str, Any]]:
        """Fetch projects by topic."""
        ...

    @abstractmethod
    def fetch_repo_detail(self, full_name: str) -> dict[str, Any]:
        """Fetch detailed info for a single repository."""
        ...

    @abstractmethod
    def search_repos(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search repositories. Returns (results, total_count)."""
        ...

    def _cache_key(self, name: str) -> str:
        """Generate a cache key filename."""
        return name.replace("/", "_").replace(" ", "_")

    def _load_cache(self, key: str) -> list[dict[str, Any]] | dict[str, Any] | None:
        """Load data from JSON cache. Returns None if not found or expired."""
        cache_file = self.json_cache_dir / f"{self._cache_key(key)}.json"
        if not cache_file.exists():
            return None

        expire_days = self.config.get("cache", {}).get("expire_days", 1)
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(days=expire_days):
            logger.debug("Cache expired for %s (age: %s)", key, datetime.now() - mtime)
            return None

        try:
            with cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("Cache hit for %s", key)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read cache %s: %s", cache_file, e)
            return None

    def _save_cache(self, key: str, data: list[dict[str, Any]] | dict[str, Any]) -> None:
        """Save data to JSON cache."""
        cache_file = self.json_cache_dir / f"{self._cache_key(key)}.json"
        try:
            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("Cached %s (%d items)", key, len(data) if isinstance(data, list) else 1)
        except OSError as e:
            logger.error("Failed to write cache %s: %s", cache_file, e)

    def _read_readme_cache(self, full_name: str) -> str | None:
        """Read cached README content."""
        cache_file = self.readme_cache_dir / f"{full_name.replace('/', '_')}.md"
        if not cache_file.exists():
            return None
        expire_days = self.config.get("render", {}).get("readme_cache_days", 7)
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(days=expire_days):
            return None
        try:
            return cache_file.read_text(encoding="utf-8")
        except OSError:
            return None

    def _save_readme_cache(self, full_name: str, content: str) -> None:
        """Cache README content."""
        cache_file = self.readme_cache_dir / f"{full_name.replace('/', '_')}.md"
        try:
            cache_file.write_text(content, encoding="utf-8")
        except OSError as e:
            logger.error("Failed to write README cache %s: %s", cache_file, e)
