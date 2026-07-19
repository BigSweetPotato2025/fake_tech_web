"""Base rendering utilities for Developer Atlas."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown as md_lib
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Language colors (sourced from GitHub Linguist)
LANGUAGE_COLORS: dict[str, str] = {
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
    "Vue": "#41B883",
    "Svelte": "#FF3E00",
    "Perl": "#0298C3",
    "Erlang": "#B83998",
    "Solidity": "#AA6746",
    "Fortran": "#4D41B1",
    "Objective-C": "#438EFF",
    "HTML": "#E34F26",
    "CSS": "#563D7C",
    "SCSS": "#C6538C",
    "Less": "#1D365D",
    "Dockerfile": "#384D54",
    "Makefile": "#427819",
    "CMake": "#DA3434",
    "TeX": "#3D6117",
    "Jupyter Notebook": "#DA5B0B",
}


def init_jinja2(template_dir: Path) -> Environment:
    """Initialize a Jinja2 environment with custom filters and globals."""
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    env.filters["format_date"] = _format_date
    env.filters["time_ago"] = _time_ago
    env.filters["stars_format"] = _stars_format
    env.filters["truncate_text"] = _truncate_text
    env.filters["language_color"] = _language_color_filter
    env.filters["markdown_to_html"] = _markdown_to_html
    env.filters["stats_format"] = _stats_format

    env.globals["format_date"] = _format_date
    env.globals["time_ago"] = _time_ago
    env.globals["stars_format"] = _stars_format
    env.globals["language_color"] = _language_color_filter
    env.globals["stats_format"] = _stats_format
    env.globals["current_year"] = datetime.now().year

    return env


def ensure_output_dir(output_dir: Path, *subdirs: str) -> Path:
    """Ensure an output subdirectory exists and return its path."""
    path = output_dir.joinpath(*subdirs) if subdirs else output_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _format_date(iso_str: str) -> str:
    """Format ISO date string to human-readable form."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return iso_str[:10] if iso_str else ""


def _time_ago(iso_str: str) -> str:
    """Convert ISO date string to relative time string."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return iso_str[:10] if iso_str else ""

    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    years = months // 12
    return f"{years}y ago"


def _stars_format(n: int) -> str:
    """Format star count to human-readable form (e.g., 1.2k, 3.5M)."""
    if not n:
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _stats_format(n: int) -> str:
    """Format stats numbers (no decimal for thousands)."""
    if not n:
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def _truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, preserving word boundaries."""
    if not text or len(text) <= max_length:
        return text or ""
    truncated = text[:max_length]
    # Try to break at a space
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    return truncated + "..."


def _language_color_filter(lang: str) -> str:
    """Return the hex color for a programming language."""
    return LANGUAGE_COLORS.get(lang, "#6366f1")


def _markdown_to_html(md_text: str) -> str:
    """Convert Markdown text to HTML."""
    if not md_text:
        return ""
    return md_lib.markdown(
        md_text,
        extensions=[
            "fenced_code",
            "codehilite",
            "tables",
            "toc",
            "nl2br",
        ],
    )


def write_html(filepath: Path, content: str) -> None:
    """Write HTML content to a file, creating parent directories."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    logger.debug("Written: %s", filepath)


def copy_assets(project_root: Path, output_dir: Path) -> None:
    """Copy static assets to output directory."""
    import shutil

    src = project_root / "assets"
    dst = output_dir / "assets"
    if src.exists():
        dst.mkdir(parents=True, exist_ok=True)
        for item in src.iterdir():
            if item.name == "images":
                continue  # Skip images, not copied
            dest = dst / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
        logger.info("Assets copied to %s", dst)
