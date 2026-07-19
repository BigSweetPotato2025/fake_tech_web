"""Projects list page renderer."""

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
    """Render projects list pages with pagination and sorting."""
    logger.info("Rendering projects pages...")

    all_repos = site_data.get("all_repos", [])
    if not all_repos:
        logger.warning("No repos to render projects pages")
        return

    total_count = len(all_repos)
    total_pages = max(1, math.ceil(total_count / PROJECTS_PER_PAGE))

    # Collect all languages for filter
    languages = sorted(set(
        r.get("language", "") for r in all_repos if r.get("language")
    ))

    # Sort options
    sort_options = ["stars", "forks", "updated", "added"]

    for sort_by in sort_options:
        if sort_by == "stars":
            sorted_repos = sorted(all_repos, key=lambda r: r.get("stars", 0), reverse=True)
        elif sort_by == "forks":
            sorted_repos = sorted(all_repos, key=lambda r: r.get("forks", 0), reverse=True)
        elif sort_by == "updated":
            sorted_repos = sorted(all_repos, key=lambda r: r.get("updated_at", ""), reverse=True)
        else:  # added
            sorted_repos = sorted(all_repos, key=lambda r: r.get("created_at", ""), reverse=True)

        for page in range(1, total_pages + 1):
            start = (page - 1) * PROJECTS_PER_PAGE
            end = start + PROJECTS_PER_PAGE
            page_repos = sorted_repos[start:end]

            if not page_repos:
                continue

            # Build pagination path
            if sort_by == "stars" and page == 1:
                page_path = output_dir / "projects" / "index.html"
            else:
                page_path = output_dir / "projects" / sort_by / str(page) / "index.html"

            base_url = "/projects/"

            html = env.get_template("projects.html").render(
                site_name=config.get("site", {}).get("name", "Developer Atlas"),
                site_description=config.get("site", {}).get("description", ""),
                site_url=config.get("site", {}).get("url", ""),
                title="Projects - Developer Atlas",
                description="Browse open source projects by stars, language, and activity.",
                current_page="projects",
                repos=page_repos,
                page=page,
                total_pages=total_pages,
                total_count=total_count,
                sort_by=sort_by,
                languages=languages,
                selected_language=None,
                search_query=None,
                search_placeholder="Search projects...",
                base_url=base_url,
                format_date=lambda x: x[:10] if x else "",
                time_ago=_time_ago,
                stars_format=_stars_format,
                language_color=_language_color_filter,
                dark_mode=False,
            )

            write_html(page_path, html)

    logger.info("  Generated %d projects pages (%d total pages x %d sorts)", 
                 total_pages * len(sort_options), total_pages, len(sort_options))
