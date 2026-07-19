"""Articles page renderer (placeholder)."""

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
    """Render the articles placeholder page."""
    logger.info("Rendering articles page...")

    html = env.get_template("articles.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Articles - Developer Atlas",
        description="Articles and insights about open source projects.",
        current_page="articles",
        articles=[],
        dark_mode=False,
    )
    write_html(output_dir / "articles" / "index.html", html)
    logger.info("  Generated articles placeholder page")
