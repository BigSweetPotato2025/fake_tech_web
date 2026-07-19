"""Statistics page renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment

from render.base import write_html, _stars_format, _time_ago, _language_color_filter

logger = logging.getLogger(__name__)


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render the statistics page."""
    logger.info("Rendering statistics page...")

    stats = site_data.get("stats", {})

    html = env.get_template("statistics.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Statistics - Developer Atlas",
        description="Open source project statistics.",
        current_page="statistics",
        stats=stats,
        stats_format=_stars_format,
        time_ago=_time_ago,
        stars_format=_stars_format,
        language_color=_language_color_filter,
        dark_mode=False,
    )
    write_html(output_dir / "statistics" / "index.html", html)
    logger.info("  Generated statistics page")
