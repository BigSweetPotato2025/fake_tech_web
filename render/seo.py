"""SEO file generator (sitemap, robots.txt, RSS feed)."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from feedgen.feed import FeedGenerator
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
    """Generate SEO files."""
    logger.info("Generating SEO files...")

    site_url = config.get("site", {}).get("url", "https://developer-atlas.example.com")
    site_name = config.get("site", {}).get("name", "Developer Atlas")
    all_repos = site_data.get("all_repos", [])
    now_str = datetime.now().isoformat()

    # robots.txt
    _generate_robots(output_dir, site_url)
    logger.info("  Generated robots.txt")

    # sitemap.xml
    _generate_sitemap(output_dir, site_url, all_repos)
    logger.info("  Generated sitemap.xml")

    # RSS feed
    _generate_rss(output_dir, site_url, site_name, all_repos)
    logger.info("  Generated RSS feed")


def _generate_robots(output_dir: Path, site_url: str) -> None:
    """Generate robots.txt."""
    content = f"""User-agent: *
Allow: /

Sitemap: {site_url}/sitemap.xml
"""
    write_html(output_dir / "robots.txt", content.strip())


def _generate_sitemap(output_dir: Path, site_url: str, repos: list[dict[str, Any]]) -> None:
    """Generate sitemap.xml."""
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Static pages
    static_pages = [
        ("/", "daily", "1.0"),
        ("/projects/", "daily", "0.9"),
        ("/topics/", "daily", "0.8"),
        ("/languages/", "weekly", "0.7"),
        ("/organizations/", "weekly", "0.7"),
        ("/collections/", "weekly", "0.7"),
        ("/articles/", "weekly", "0.5"),
        ("/statistics/", "daily", "0.6"),
    ]
    for path, changefreq, priority in static_pages:
        url = SubElement(urlset, "url")
        loc = SubElement(url, "loc")
        loc.text = f"{site_url}{path}"
        cf = SubElement(url, "changefreq")
        cf.text = changefreq
        pr = SubElement(url, "priority")
        pr.text = priority

    # Project pages
    for repo in repos:
        full_name = repo.get("full_name", "")
        if not full_name:
            continue
        url = SubElement(urlset, "url")
        loc = SubElement(url, "loc")
        loc.text = f"{site_url}/projects/{full_name}/"
        lastmod = SubElement(url, "lastmod")
        lastmod.text = repo.get("updated_at", "")[:10] or datetime.now().strftime("%Y-%m-%d")
        cf = SubElement(url, "changefreq")
        cf.text = "weekly"
        pr = SubElement(url, "priority")
        pr.text = "0.6"

    # Topics pages
    topic_names = set()
    for repo in repos:
        for topic in repo.get("topics", []):
            if topic not in topic_names:
                topic_names.add(topic)

    for topic in topic_names:
        url = SubElement(urlset, "url")
        loc = SubElement(url, "loc")
        loc.text = f"{site_url}/topics/{topic}/"
        pr = SubElement(url, "priority")
        pr.text = "0.5"

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content = tostring(urlset, encoding="unicode")
    (output_dir / "sitemap.xml").write_text(xml_declaration + xml_content, encoding="utf-8")


def _generate_rss(output_dir: Path, site_url: str, site_name: str, repos: list[dict[str, Any]]) -> None:
    """Generate RSS feed."""
    fg = FeedGenerator()
    fg.title(site_name)
    fg.description("Discover the best open source projects. Curated for developers, updated daily.")
    fg.link(href=site_url, rel="alternate")
    fg.link(href=f"{site_url}/feed.xml", rel="self")
    fg.language("en")

    # Add recent projects
    sorted_repos = sorted(repos, key=lambda r: r.get("updated_at", ""), reverse=True)[:50]
    for repo in sorted_repos:
        full_name = repo.get("full_name", "")
        if not full_name:
            continue
        fe = fg.add_entry()
        fe.title(f"{full_name} - {repo.get('description', '')[:100]}" if repo.get('description') else full_name)
        fe.link(href=f"{site_url}/projects/{full_name}/")
        fe.description(repo.get("description", "") or "No description")
        fe.guid(f"{site_url}/projects/{full_name}/", permalink=True)

        updated = repo.get("updated_at", "")
        if updated:
            try:
                fe.updated(updated)
            except Exception:
                pass

        author = repo.get("owner", "")
        if author:
            fe.author(name=author)

    fg.rss_file(str(output_dir / "feed.xml"), pretty=True)
