"""Topics page renderer."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from jinja2 import Environment

from render.base import write_html, _stars_format, _time_ago, _language_color_filter

logger = logging.getLogger(__name__)

PROJECTS_PER_PAGE = 30


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render topics list and topic detail pages."""
    logger.info("Rendering topics pages...")

    topic_repos = site_data.get("topics", {})
    topics_config = config.get("topics", [])

    # Topics list page
    topics_list = []
    for t in topics_config:
        name = t["name"]
        repos = topic_repos.get(name, [])
        topics_list.append({
            "name": name,
            "display_name": t.get("display_name", name),
            "description": t.get("description", ""),
            "count": len(repos),
            "color": t.get("color", "#6366f1"),
        })
    topics_list.sort(key=lambda t: t["count"], reverse=True)

    html = env.get_template("topics.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Topics - Developer Atlas",
        description="Browse open source projects by topic.",
        current_page="topics",
        topics=topics_list,
        time_ago=_time_ago,
        stars_format=_stars_format,
        language_color=_language_color_filter,
        dark_mode=False,
    )
    write_html(output_dir / "topics" / "index.html", html)

    # Topic detail pages
    for t in topics_config:
        name = t["name"]
        repos = topic_repos.get(name, [])
        if not repos:
            continue

        repos.sort(key=lambda r: r.get("stars", 0), reverse=True)
        total_pages = max(1, math.ceil(len(repos) / PROJECTS_PER_PAGE))

        for page in range(1, total_pages + 1):
            start = (page - 1) * PROJECTS_PER_PAGE
            end = start + PROJECTS_PER_PAGE
            page_repos = repos[start:end]
            if not page_repos:
                continue

            if page == 1:
                page_path = output_dir / "topics" / name / "index.html"
            else:
                page_path = output_dir / "topics" / name / "page" / str(page) / "index.html"

            html = env.get_template("topic_detail.html").render(
                site_name=config.get("site", {}).get("name", "Developer Atlas"),
                site_description=config.get("site", {}).get("description", ""),
                site_url=config.get("site", {}).get("url", ""),
                title=f"{t.get('display_name', name)} - Topics - Developer Atlas",
                description=f"Browse {t.get('display_name', name)} open source projects.",
                topic_desc=t.get("description", ""),
                current_page="topics",
                name=name,
                display_name=t.get("display_name", name),
                color=t.get("color", ""),
                repos=page_repos,
                page=page,
                total_pages=total_pages,
                time_ago=_time_ago,
                stars_format=_stars_format,
                language_color=_language_color_filter,
                dark_mode=False,
            )
            write_html(page_path, html)

    logger.info("  Generated %d topic pages", len(topics_config))
