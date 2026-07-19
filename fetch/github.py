"""GitHub API fetcher for Developer Atlas."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from fetch.base import BaseFetcher

logger = logging.getLogger(__name__)


class GitHubFetcher(BaseFetcher):
    """Fetches repository data from GitHub REST API v3."""

    API_BASE = "https://api.github.com"

    def __init__(self, config: dict, cache_dir: Path):
        super().__init__(config, cache_dir)
        github_config = config.get("github", {})
        self.token = github_config.get("token", "")
        self.per_page = github_config.get("per_page", 100)
        self.request_delay = github_config.get("request_delay", 1.0)
        self._session = self._create_session()
        self._last_request_time = 0.0

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Developer-Atlas/1.0",
        })
        if self.token:
            session.headers.update({"Authorization": f"token {self.token}"})
        return session

    def _rate_limit_wait(self, response: requests.Response) -> None:
        """Check rate limit headers and wait if needed."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) < 10:
            reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
            wait = max(reset_time - time.time(), 0) + 1
            if wait > 0:
                logger.warning("Rate limit low (%s remaining), waiting %.0fs", remaining, wait)
                time.sleep(wait)

    def _respect_delay(self) -> None:
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

    def _request(self, url: str, params: dict | None = None) -> requests.Response | None:
        """Make a rate-limited, delayed HTTP request with retry."""
        max_retries = 3
        for attempt in range(max_retries):
            self._respect_delay()
            try:
                resp = self._session.get(url, params=params, timeout=30)
                self._last_request_time = time.time()
                self._rate_limit_wait(resp)

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", "60"))
                    logger.warning("Rate limited, waiting %ds (attempt %d/%d)", retry_after, attempt + 1, max_retries)
                    time.sleep(retry_after)
                    continue

                if resp.status_code == 404:
                    return None

                if resp.status_code == 403:
                    logger.warning("Forbidden (attempt %d/%d): %s", attempt + 1, max_retries, url)
                    time.sleep(10)
                    continue

                resp.raise_for_status()
                return resp

            except requests.RequestException as e:
                logger.warning("Request failed (attempt %d/%d): %s - %s", attempt + 1, max_retries, url, e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("Request failed after %d attempts: %s", max_retries, url)
                    return None

        return None

    def _paginate(self, url: str, params: dict | None = None, max_pages: int = 5) -> list[dict[str, Any]]:
        """Fetch all pages from a paginated API endpoint."""
        results: list[dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            page_params = dict(params or {})
            page_params["per_page"] = self.per_page
            page_params["page"] = page

            resp = self._request(url, params=page_params)
            if resp is None:
                break

            page_data = resp.json()
            if not page_data:
                break

            results.extend(page_data if isinstance(page_data, list) else page_data.get("items", []))

            # Check for next page via Link header
            link_header = resp.headers.get("Link", "")
            if not re.search(r'rel="next"', link_header):
                break

            page += 1

        return results

    def _normalize_repo(self, repo: dict[str, Any]) -> dict[str, Any]:
        """Normalize GitHub API response to unified format."""
        license_name = None
        if repo.get("license"):
            license_name = repo["license"].get("spdx_id") or repo["license"].get("key")

        return {
            "id": repo.get("id", 0),
            "name": repo.get("name", ""),
            "owner": repo.get("owner", {}).get("login", ""),
            "owner_url": repo.get("owner", {}).get("html_url", ""),
            "owner_avatar": repo.get("owner", {}).get("avatar_url", ""),
            "full_name": repo.get("full_name", ""),
            "description": repo.get("description") or "",
            "url": repo.get("html_url", ""),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language") or "",
            "license_name": license_name,
            "topics": repo.get("topics", []),
            "homepage": repo.get("homepage") or "",
            "created_at": repo.get("created_at", ""),
            "updated_at": repo.get("updated_at", ""),
            "default_branch": repo.get("default_branch", "main"),
            "open_issues": repo.get("open_issues_count", 0),
            "latest_release_name": None,
            "latest_release_url": None,
            "latest_release_tag": None,
            "latest_release_published": None,
            "readme": None,
        }

    def _fetch_latest_release(self, full_name: str) -> dict[str, Any]:
        """Fetch the latest release for a repository."""
        url = f"{self.API_BASE}/repos/{full_name}/releases/latest"
        resp = self._request(url)
        if resp is None:
            return {}
        data = resp.json()
        return {
            "latest_release_name": data.get("name") or data.get("tag_name", ""),
            "latest_release_url": data.get("html_url", ""),
            "latest_release_tag": data.get("tag_name", ""),
            "latest_release_published": data.get("published_at", ""),
        }

    def _fetch_readme(self, full_name: str) -> str | None:
        """Fetch README content for a repository."""
        # Check cache first
        cached = self._read_readme_cache(full_name)
        if cached is not None:
            return cached

        url = f"{self.API_BASE}/repos/{full_name}/readme"
        resp = self._request(url, params={"Accept": "application/vnd.github.raw"})
        if resp is None:
            return None

        content = resp.text
        max_size = self.config.get("render", {}).get("max_readme_size", 102400)
        if len(content) > max_size:
            content = content[:max_size] + "\n\n*README truncated due to size*"

        self._save_readme_cache(full_name, content)
        return content

    def fetch_trending(self) -> list[dict[str, Any]]:
        """Fetch trending repositories (high stars, recently pushed)."""
        cache_key = "trending"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = f"{self.API_BASE}/search/repositories"
        params = {
            "q": f"pushed:>={seven_days_ago} stars:>10",
            "sort": "stars",
            "order": "desc",
        }
        results = self._paginate(url, params, max_pages=2)
        repos = [self._normalize_repo(r) for r in results]
        self._save_cache(cache_key, repos)
        logger.info("Fetched %d trending repositories", len(repos))
        return repos

    def fetch_recently_updated(self) -> list[dict[str, Any]]:
        """Fetch recently updated repositories (quality-filtered)."""
        cache_key = "recently_updated"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        url = f"{self.API_BASE}/search/repositories"
        params = {
            "q": f"pushed:>={three_days_ago} stars:>10",
            "sort": "updated",
            "order": "desc",
        }
        results = self._paginate(url, params, max_pages=2)
        repos = [self._normalize_repo(r) for r in results]
        self._save_cache(cache_key, repos)
        logger.info("Fetched %d recently updated repositories", len(repos))
        return repos

    def fetch_by_topic(self, topic: str) -> list[dict[str, Any]]:
        """Fetch repositories by topic."""
        cache_key = f"topic_{topic}"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        url = f"{self.API_BASE}/search/repositories"
        params = {
            "q": f"topic:{topic}",
            "sort": "stars",
            "order": "desc",
        }
        results = self._paginate(url, params, max_pages=3)
        repos = [self._normalize_repo(r) for r in results]
        self._save_cache(cache_key, repos)
        logger.info("Fetched %d repositories for topic '%s'", len(repos), topic)
        return repos

    def fetch_repo_detail(self, full_name: str) -> dict[str, Any]:
        """Fetch detailed info for a single repository including README and latest release."""
        cache_key = f"detail_{full_name.replace('/', '_')}"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        url = f"{self.API_BASE}/repos/{full_name}"
        resp = self._request(url)
        if resp is None:
            return {}

        repo = self._normalize_repo(resp.json())

        # Fetch latest release
        release_data = self._fetch_latest_release(full_name)
        repo.update(release_data)

        # Fetch README
        repo["readme"] = self._fetch_readme(full_name)

        self._save_cache(cache_key, repo)
        logger.info("Fetched detail for %s", full_name)
        return repo

    def search_repos(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        page: int = 1,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search repositories using GitHub search API."""
        url = f"{self.API_BASE}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": 30,
            "page": page,
        }

        resp = self._request(url, params=params)
        if resp is None:
            return [], 0

        data = resp.json()
        repos = [self._normalize_repo(r) for r in data.get("items", [])]
        total = data.get("total_count", 0)
        logger.info("Search '%s': found %d results, returned %d", query, total, len(repos))
        return repos, total

    def fetch_latest_releases(self) -> list[dict[str, Any]]:
        """Fetch repositories with recent releases."""
        cache_key = "latest_releases"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = f"{self.API_BASE}/search/repositories"
        params = {
            "q": f"pushed:>={seven_days_ago}",
            "sort": "updated",
            "order": "desc",
        }
        results = self._paginate(url, params, max_pages=2)

        repos = []
        for r in results:
            repo = self._normalize_repo(r)
            release_data = self._fetch_latest_release(r["full_name"])
            repo.update(release_data)
            if repo["latest_release_tag"]:
                repos.append(repo)

        self._save_cache(cache_key, repos)
        logger.info("Fetched %d repositories with recent releases", len(repos))
        return repos
