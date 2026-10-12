#!/usr/bin/env python3
"""Developer Atlas — Static site builder entry point.

Usage:
    python builder/build.py                  # Full build (fetch + render)
    python builder/build.py --clean          # Clean + full build
    python builder/build.py --skip-fetch     # Use cached data, render only
    python builder/build.py --skip-render    # Fetch data only, no HTML
    python builder/build.py --config path/to/config.yaml

Data source:
    GitHub REST API — every site fetches independently with its own token
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

import yaml

# Allow running as `python builder/build.py` without PYTHONPATH
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from builder.clean import clean_cache, clean_output

logger = logging.getLogger("developer-atlas")


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        logger.error("Config file not found: %s", path.absolute())
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        logger.error("Empty config file: %s", path)
        sys.exit(1)

    # Merge secret.yaml (same directory, overrides config)
    secret_path = path.parent / "secret.yaml"
    if secret_path.exists():
        with secret_path.open("r", encoding="utf-8") as f:
            secret = yaml.safe_load(f) or {}
        for key, value in secret.items():
            config.setdefault(key, {}).update(value)
        logger.info("Loaded secrets from %s", secret_path)

    logger.info("Loaded config from %s", path)
    return config


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root = logging.getLogger("developer-atlas")
    root.setLevel(level)
    root.addHandler(handler)

    # Silence noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_project_root() -> Path:
    """Get the project root directory (parent of builder/)."""
    return Path(__file__).resolve().parent.parent


def build(
    config: dict,
    project_root: Path,
    skip_fetch: bool = False,
    skip_render: bool = False,
) -> bool:
    """Run the full build pipeline."""
    cache_dir = project_root / config.get("cache", {}).get("json_dir", "cache")
    output_dir = Path(config.get("render", {}).get("output_dir", "dist"))
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir

    site_data: dict = {}

    # Step 1: Fetch
    if not skip_fetch:
        logger.info("=== Step 1: Fetch ===")
        from fetch.github import GitHubFetcher
        fetcher = GitHubFetcher(config, cache_dir)

        trending = fetcher.fetch_trending()
        recently_updated = fetcher.fetch_recently_updated()
        latest_releases = fetcher.fetch_latest_releases()

        # Fetch by configured topics
        topic_repos: dict[str, list] = {}
        topics_config = config.get("topics", [])
        for topic_cfg in topics_config:
            name = topic_cfg["name"]
            logger.info("Fetching topic: %s", name)
            repos = fetcher.fetch_by_topic(name)
            if repos:
                topic_repos[name] = repos

        site_data = {
            "all_repos": [],
            "trending": trending,
            "recently_updated": recently_updated,
            "latest_releases": latest_releases,
            "topics": topic_repos,
        }

        # Build all_repos from all sources (dedup)
        seen: set[str] = set()
        all_repos = []
        for repo in trending + recently_updated:
            if repo.get("full_name") and repo["full_name"] not in seen:
                seen.add(repo["full_name"])
                all_repos.append(repo)

        # Add topic repos
        for topic_name, repos in topic_repos.items():
            for repo in repos:
                if repo.get("full_name") and repo["full_name"] not in seen:
                    seen.add(repo["full_name"])
                    all_repos.append(repo)

        site_data["all_repos"] = all_repos
        logger.info("Total unique repos: %d", len(all_repos))
    else:
        logger.info("=== Step 1: Fetch (skipped) ===")
        # Load from cache
        import json as json_module
        json_cache = cache_dir / "json"
        if json_cache.exists():
            for f in json_cache.glob("*.json"):
                key = f.stem
                try:
                    data = json_module.loads(f.read_text(encoding="utf-8"))
                    site_data[key] = data
                except (json_module.JSONDecodeError, OSError) as e:
                    logger.warning("Failed to load cache %s: %s", f, e)

    # Step 2: Render
    if not skip_render:
        logger.info("=== Step 2: Render ===")
        from render.base import init_jinja2
        from render.index import render as render_index
        from render.projects import render as render_projects
        from render.project_detail import render as render_project_detail
        from render.topics import render as render_topics
        from render.languages import render as render_languages
        from render.organizations import render as render_organizations
        from render.collections import render as render_collections
        from render.articles import render as render_articles
        from render.statistics import render as render_statistics
        from render.seo import render as render_seo

        template_dir = project_root / "templates"
        env = init_jinja2(template_dir)

        # Compute statistics
        all_repos = site_data.get("all_repos", [])

        # Language stats
        lang_map: dict[str, int] = {}
        for repo in all_repos:
            lang = repo.get("language")
            if lang:
                lang_map[lang] = lang_map.get(lang, 0) + 1

        # Org stats
        org_map: dict[str, dict] = {}
        for repo in all_repos:
            owner = repo.get("owner", "")
            if owner:
                if owner not in org_map:
                    org_map[owner] = {
                        "name": owner,
                        "display_name": owner,
                        "count": 0,
                        "avatar_url": repo.get("owner_avatar", ""),
                    }
                org_map[owner]["count"] += 1

        langs_sorted = sorted(lang_map.items(), key=lambda x: x[1], reverse=True)
        orgs_sorted = sorted(org_map.values(), key=lambda x: x["count"], reverse=True)

        all_stars = sum(r.get("stars", 0) for r in all_repos)
        all_forks = sum(r.get("forks", 0) for r in all_repos)

        stats = {
            "overview": {
                "total_projects": len(all_repos),
                "total_stars": all_stars,
                "total_forks": all_forks,
                "total_topics": len(config.get("topics", [])),
                "total_languages": len(lang_map),
                "total_organizations": len(org_map),
            },
            "top_languages": [
                {"name": name, "count": count, "color": _language_color(name)}
                for name, count in langs_sorted
            ],
            "most_active_orgs": list(orgs_sorted),
            "fastest_growing": sorted(
                all_repos, key=lambda r: r.get("stars", 0), reverse=True
            )[:20],
            "newest": sorted(
                all_repos, key=lambda r: r.get("created_at", ""), reverse=True
            )[:20],
            "largest": sorted(
                all_repos, key=lambda r: r.get("stars", 0), reverse=True
            )[:20],
        }

        site_data["stats"] = stats
        site_data["languages"] = lang_map
        site_data["organizations"] = org_map
        site_data["config"] = config

        output_dir.mkdir(parents=True, exist_ok=True)

        # Render all pages
        render_index(env, cache_dir, output_dir, config, site_data)
        render_projects(env, cache_dir, output_dir, config, site_data)
        render_project_detail(env, cache_dir, output_dir, config, site_data)
        render_topics(env, cache_dir, output_dir, config, site_data)
        render_languages(env, cache_dir, output_dir, config, site_data)
        render_organizations(env, cache_dir, output_dir, config, site_data)
        render_collections(env, cache_dir, output_dir, config, site_data)
        render_articles(env, cache_dir, output_dir, config, site_data)
        render_statistics(env, cache_dir, output_dir, config, site_data)
        render_seo(env, cache_dir, output_dir, config, site_data)

        logger.info("Render complete. Output: %s", output_dir)
    else:
        logger.info("=== Step 2: Render (skipped) ===")

    return True


def _language_color(lang: str) -> str:
    """Return a color for a programming language."""
    colors = {
        "Python": "#3572A5",
        "Go": "#00ADD8",
        "Rust": "#DEA584",
        "Java": "#B07219",
        "TypeScript": "#3178C6",
        "JavaScript": "#F7DF1E",
        "C": "#555555",
        "C++": "#F34B7D",
        "C#": "#178600",
        "Shell": "#89E051",
        "Ruby": "#701516",
        "PHP": "#4F5D95",
        "Swift": "#F05138",
        "Kotlin": "#A97BFF",
        "Dart": "#00B4AB",
        "Scala": "#C22D40",
        "Haskell": "#5E5086",
        "Lua": "#000080",
        "Elixir": "#6E4A7E",
        "Clojure": "#DB5855",
        "Zig": "#EC915C",
        "Nix": "#7EBAEF",
        "R": "#198CE7",
        "Julia": "#A270BA",
    }
    return colors.get(lang, "#6366f1")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Developer Atlas - Static Site Builder"
    )
    parser.add_argument("--clean", action="store_true", help="Clean cache and output before building")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetching, use cached data")
    parser.add_argument("--skip-render", action="store_true", help="Skip rendering")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--output", default=None, help="Output directory override")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)
    project_root = get_project_root()

    # Resolve config path
    config_path = args.config
    if not Path(config_path).is_absolute():
        config_path = str(project_root / config_path)

    config = load_config(config_path)

    if args.output:
        config.setdefault("render", {})["output_dir"] = args.output

    # Clean if requested
    if args.clean:
        logger.info("=== Clean ===")
        cache_dir = project_root / config.get("cache", {}).get("json_dir", "cache")
        output_dir = Path(config.get("render", {}).get("output_dir", "dist"))
        if not output_dir.is_absolute():
            output_dir = project_root / output_dir
        clean_cache(cache_dir)
        clean_output(output_dir)

    # Build
    success = build(config, project_root, args.skip_fetch, args.skip_render)

    if success:
        logger.info("=== Build complete ===")
        output_dir = config.get("render", {}).get("output_dir", "dist")
        logger.info("Output: %s", output_dir)

        # Copy compiled Tailwind CSS to dist if it exists
        src_css = project_root / "assets" / "css" / "output.css"
        dst_css = project_root / output_dir / "assets" / "css" / "output.css"
        if src_css.exists():
            dst_css.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_css, dst_css)
            logger.info("Copied output.css to %s", dst_css)
        else:
            logger.warning("output.css not found at %s — run Tailwind build first", src_css)
    else:
        logger.error("=== Build failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
