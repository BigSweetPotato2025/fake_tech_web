"""Home page renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment

from render.base import write_html, copy_assets

logger = logging.getLogger(__name__)


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render the home page."""
    logger.info("Rendering home page...")

    all_repos = site_data.get("all_repos", [])
    trending = site_data.get("trending", [])
    latest_releases = site_data.get("latest_releases", [])
    stats = site_data.get("stats", {})

    # Latest projects: sort by stars (default for all pages)
    latest = sorted(all_repos, key=lambda r: r.get("stars", 0), reverse=True)[:12]

    # Popular topics: from config with counts
    topics_config = config.get("topics", [])
    topic_repos = site_data.get("topics", {})
    popular_topics = []
    for t in topics_config:
        name = t["name"]
        repos = topic_repos.get(name, [])
        popular_topics.append({
            "name": name,
            "display_name": t.get("display_name", name),
            "description": t.get("description", ""),
            "count": len(repos),
            "color": t.get("color", "#6366f1"),
        })
    popular_topics.sort(key=lambda t: t["count"], reverse=True)

    # Featured collections from config
    collections_config = [
        {"name": "Awesome AI", "description": "Artificial intelligence and machine learning projects", "count": 0},
        {"name": "Awesome Docker", "description": "Containerization and orchestration tools", "count": 0},
        {"name": "Awesome Rust", "description": "Rust programming language ecosystem", "count": 0},
        {"name": "Awesome Linux", "description": "Linux system tools and utilities", "count": 0},
        {"name": "Awesome Self-hosted", "description": "Self-hosted software and services", "count": 0},
    ]
    for coll in collections_config:
        key = coll["name"].replace("Awesome ", "").lower()
        repos = topic_repos.get(key, [])
        coll["count"] = len(repos)
        coll["repos"] = repos[:6]

    # Weekly picks: top by stars
    weekly = sorted(all_repos, key=lambda r: r.get("stars", 0), reverse=True)[:6]

    # Compute stats for banner
    overview = stats.get("overview", {})
    banner_stats = {
        "total_projects": overview.get("total_projects", len(all_repos)),
        "total_topics": len(topics_config),
        "total_languages": overview.get("total_languages", 0),
        "total_organizations": overview.get("total_organizations", 0),
        "total_github_stars": overview.get("total_stars", sum(r.get("stars", 0) for r in all_repos)),
        "last_updated": max(
            (r.get("updated_at", "") for r in all_repos if r.get("updated_at")),
            default="",
        ),
    }

    html = env.get_template("index.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Developer Atlas - Discover Great Open Source Projects",
        description="Curated collection of the best open source projects. Updated daily.",
        current_page="home",
        latest_projects=latest,
        trending_projects=trending[:8],
        latest_releases=latest_releases[:6],
        popular_topics=popular_topics,
        featured_collections=collections_config,
        weekly_picks=weekly,
        stats=banner_stats,
        dark_mode=False,
    )

    write_html(output_dir / "index.html", html)
    logger.info("  Generated index.html")

    # Copy assets
    project_root = output_dir.parent
    copy_assets(project_root, output_dir)
