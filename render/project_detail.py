"""Project detail page renderer."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment
import markdown as md_lib

from render.base import write_html, _stars_format, _time_ago, _language_color_filter, _format_date

logger = logging.getLogger(__name__)


def render(
    env: Environment,
    cache_dir: Path,
    output_dir: Path,
    config: dict,
    site_data: dict,
) -> None:
    """Render individual project detail pages."""
    logger.info("Rendering project detail pages...")

    all_repos = site_data.get("all_repos", [])
    if not all_repos:
        logger.warning("No repos to render detail pages")
        return

    # Build a lookup by full_name
    repo_map: dict[str, dict] = {}
    for repo in all_repos:
        full_name = repo.get("full_name", "")
        if full_name:
            repo_map[full_name] = repo

    count = 0
    for repo in all_repos:
        full_name = repo.get("full_name", "")
        if not full_name:
            continue

        # Find related projects (same topics)
        repo_topics = set(repo.get("topics", []))
        related = []
        for other in all_repos:
            if other.get("full_name") == full_name:
                continue
            other_topics = set(other.get("topics", []))
            if repo_topics and other_topics and repo_topics & other_topics:
                related.append(other)
        # Sort related by stars, take top 6
        related.sort(key=lambda r: r.get("stars", 0), reverse=True)
        related = related[:6]

        # README from cache
        readme_html = ""
        readme_cache = cache_dir / "readme" / f"{full_name.replace('/', '_')}.md"
        if readme_cache.exists():
            try:
                md_content = readme_cache.read_text(encoding="utf-8")
                readme_html = md_lib.markdown(
                    md_content,
                    extensions=["fenced_code", "codehilite", "tables", "toc", "nl2br"],
                )
            except OSError:
                pass
        elif repo.get("readme"):
            readme_html = md_lib.markdown(
                repo["readme"],
                extensions=["fenced_code", "codehilite", "tables", "toc", "nl2br"],
            )

        output_path = output_dir / "projects" / full_name / "index.html"

        html = env.get_template("project_detail.html").render(
            site_name=config.get("site", {}).get("name", "Developer Atlas"),
            site_description=config.get("site", {}).get("description", ""),
            site_url=config.get("site", {}).get("url", ""),
            title=f"{full_name} - Developer Atlas",
            description=repo.get("description", ""),
            current_page="projects",
            repo=repo,
            related_projects=related,
            readme_html=readme_html,
            format_date=_format_date,
            time_ago=_time_ago,
            stars_format=_stars_format,
            language_color=_language_color_filter,
            dark_mode=False,
        )

        write_html(output_path, html)
        count += 1

    logger.info("  Generated %d project detail pages", count)

    # Generate search index JSON
    _generate_search_index(output_dir, all_repos)


def _generate_search_index(output_dir: Path, repos: list[dict[str, Any]]) -> None:
    """Generate search.json for front-end search."""
    search_index = []
    for repo in repos:
        search_index.append({
            "full_name": repo.get("full_name", ""),
            "name": repo.get("name", ""),
            "owner": repo.get("owner", ""),
            "description": repo.get("description", ""),
            "url": repo.get("url", ""),
            "stars": repo.get("stars", 0),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", []),
        })

    json_dir = output_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    json_path = json_dir / "search.json"
    json_path.write_text(
        json.dumps(search_index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    logger.info("  Generated search.json (%d entries)", len(search_index))
