"""Organizations page renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment

from render.base import write_html

logger = logging.getLogger(__name__)


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render the organizations overview page."""
    logger.info("Rendering organizations page...")

    all_repos = site_data.get("all_repos", [])

    # Aggregate by owner
    org_map: dict[str, dict] = {}
    for repo in all_repos:
        owner = repo.get("owner", "")
        if not owner:
            continue
        if owner not in org_map:
            org_map[owner] = {
                "name": owner,
                "display_name": owner,
                "description": "",
                "count": 0,
                "avatar_url": repo.get("owner_avatar", ""),
            }
        org_map[owner]["count"] += 1

    organizations = sorted(org_map.values(), key=lambda o: o["count"], reverse=True)

    html = env.get_template("organizations.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Organizations - Developer Atlas",
        description="Browse open source projects by organization.",
        current_page="organizations",
        organizations=organizations,
        dark_mode=False,
    )
    write_html(output_dir / "organizations" / "index.html", html)
    logger.info("  Generated organizations page with %d organizations", len(organizations))
