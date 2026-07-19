"""Collections page renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment

from render.base import write_html, _stars_format

logger = logging.getLogger(__name__)


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render the collections page."""
    logger.info("Rendering collections page...")

    topic_repos = site_data.get("topics", {})
    all_repos = site_data.get("all_repos", [])

    # Define collections based on topics
    collection_defs = [
        {"name": "Awesome AI", "description": "Artificial intelligence and machine learning projects", "topic_key": "ai"},
        {"name": "Awesome Docker", "description": "Containerization and orchestration tools", "topic_key": "docker"},
        {"name": "Awesome Rust", "description": "Rust programming language ecosystem", "topic_key": "rust"},
        {"name": "Awesome Linux", "description": "Linux system tools and utilities", "topic_key": "linux"},
        {"name": "Awesome Self-hosted", "description": "Self-hosted software and services", "topic_key": "self-hosted"},
        {"name": "Awesome CLI", "description": "Command-line tools and utilities", "topic_key": "cli"},
        {"name": "Awesome Security", "description": "Security tools and practices", "topic_key": "security"},
        {"name": "Awesome Web", "description": "Web development frameworks and libraries", "topic_key": "web"},
    ]

    collections = []
    for cd in collection_defs:
        repos = topic_repos.get(cd["topic_key"], [])
        # If no topic repos, try to find by language
        if not repos and cd["topic_key"] == "rust":
            repos = [r for r in all_repos if r.get("language") == "Rust"][:30]
        collections.append({
            "name": cd["name"],
            "description": cd["description"],
            "count": len(repos),
            "repos": repos[:12],
        })

    html = env.get_template("collections.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Collections - Developer Atlas",
        description="Curated collections of open source projects.",
        current_page="collections",
        collections=collections,
        stars_format=_stars_format,
        dark_mode=False,
    )
    write_html(output_dir / "collections" / "index.html", html)
    logger.info("  Generated collections page with %d collections", len(collections))
