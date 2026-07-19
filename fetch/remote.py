"""Remote HTTP fetcher — pulls cached data from a master site instead of GitHub API.

Used by sub-sites that don't have a GitHub token.
The master site runs GitHubFetcher, then exports cache/ to dist/cache/.
Sub-sites use RemoteFetcher to download those cache files over HTTPS.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import requests

from fetch.base import BaseFetcher

logger = logging.getLogger(__name__)


class RemoteFetcher(BaseFetcher):
    """Fetcher that downloads pre-cached data from a master site over HTTP.

    Config required in config.yaml:
      fetch:
        mode: remote
        remote_url: "https://master.example.com/cache/"
        cache_token: "your-shared-secret"   # optional, for header auth
    """

    def __init__(self, config: dict, cache_dir: Path):
        super().__init__(config, cache_dir)
        fetch_config = config.get("fetch", {})
        self.remote_base = fetch_config.get("remote_url", "").rstrip("/")
        self.cache_token = fetch_config.get("cache_token", "")

        if not self.remote_base:
            raise ValueError(
                "fetch.remote_url must be set in config.yaml when fetch.mode=remote"
            )

        logger.info("RemoteFetcher: master = %s", self.remote_base)

    # ── Internal HTTP helpers ───────────────────────────

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "User-Agent": "Developer-Atlas/1.0",
            "Accept": "application/json",
        }
        if self.cache_token:
            headers["X-Cache-Token"] = self.cache_token
        return headers

    def _fetch_json(self, path: str) -> list[dict[str, Any]] | dict[str, Any]:
        """Download a JSON file from the master and save into local cache."""
        url = f"{self.remote_base}/{path.lstrip('/')}"
        logger.debug("Downloading %s", url)

        resp = requests.get(url, headers=self._headers(), timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # Write to local cache
        cache_key = path.removesuffix(".json").replace("/", "_")
        cache_file = self.json_cache_dir / f"{cache_key}.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(resp.text, encoding="utf-8")
        logger.debug("Cached to %s", cache_file)

        return data

    def _fetch_readme(self, full_name: str) -> str | None:
        """Download a README file from the master and save into local cache."""
        filename = f"{full_name.replace('/', '_')}.md"
        url = f"{self.remote_base}/readme/{filename}"
        logger.debug("Downloading README %s", url)

        try:
            resp = requests.get(url, headers=self._headers(), timeout=120)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning("Failed to download README %s: %s", full_name, e)
            return None

        cache_file = self.readme_cache_dir / filename
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(resp.text, encoding="utf-8")

        return resp.text

    # ── BaseFetcher interface ───────────────────────────

    def fetch_trending(self) -> list[dict[str, Any]]:
        data = self._fetch_json("json/trending.json")
        return data if isinstance(data, list) else []

    def fetch_recently_updated(self) -> list[dict[str, Any]]:
        data = self._fetch_json("json/recently_updated.json")
        return data if isinstance(data, list) else []

    def fetch_latest_releases(self) -> list[dict[str, Any]]:
        data = self._fetch_json("json/latest_releases.json")
        return data if isinstance(data, list) else []

    def fetch_by_topic(self, topic: str) -> list[dict[str, Any]]:
        key = f"topic_{topic}"
        data = self._fetch_json(f"json/{key}.json")
        return data if isinstance(data, list) else []

    def fetch_repo_detail(self, full_name: str) -> dict[str, Any]:
        key = f"detail_{full_name.replace('/', '_')}"
        data = self._fetch_json(f"json/{key}.json")
        if not data:
            return {}
        # Also fetch README separately
        if isinstance(data, dict):
            readme = self._fetch_readme(full_name)
            if readme is not None:
                data["readme"] = readme
        return data if isinstance(data, dict) else {}

    def search_repos(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
    ) -> tuple[list[dict[str, Any]], int]:
        """Not supported in remote mode. Fallback to local cache scan."""
        logger.warning("search_repos not supported in remote mode, scanning local cache")
        from fetch.github import GitHubFetcher

        # Use GitHubFetcher's search as fallback on local cache
        import json
        results = []
        for f in sorted(self.json_cache_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    results.extend(data)
                elif isinstance(data, dict) and data.get("full_name"):
                    results.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        # Dedup
        seen: set[str] = set()
        unique = []
        for r in results:
            fn = r.get("full_name", "")
            if fn and fn not in seen:
                seen.add(fn)
                unique.append(r)

        return unique, len(unique)
