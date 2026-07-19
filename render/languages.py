"""Languages page renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment

from render.base import write_html, _language_color_filter

logger = logging.getLogger(__name__)


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render the languages overview page."""
    logger.info("Rendering languages page...")

    all_repos = site_data.get("all_repos", [])

    # Count repos per language
    lang_counts: dict[str, int] = {}
    for repo in all_repos:
        lang = repo.get("language", "")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    languages = sorted(
        [
            {"name": name, "count": count, "color": _language_color_filter(name)}
            for name, count in lang_counts.items()
        ],
        key=lambda l: l["count"],
        reverse=True,
    )

    html = env.get_template("languages.html").render(
        site_name=config.get("site", {}).get("name", "Developer Atlas"),
        site_description=config.get("site", {}).get("description", ""),
        site_url=config.get("site", {}).get("url", ""),
        title="Languages - Developer Atlas",
        description="Browse open source projects by programming language.",
        current_page="languages",
        languages=languages,
        dark_mode=False,
    )
    write_html(output_dir / "languages" / "index.html", html)
    logger.info("  Generated languages page with %d languages", len(languages))
