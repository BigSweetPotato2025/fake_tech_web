"""Cache and output cleaning utilities."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def clean_cache(cache_dir: Path) -> None:
    """Clean all cached data (JSON + README)."""
    json_dir = cache_dir / "json"
    readme_dir = cache_dir / "readme"

    if json_dir.exists():
        count = len(list(json_dir.glob("*.json")))
        shutil.rmtree(json_dir)
        json_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cleaned %d JSON cache files from %s", count, json_dir)

    if readme_dir.exists():
        count = len(list(readme_dir.glob("*.md")))
        shutil.rmtree(readme_dir)
        readme_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Cleaned %d README cache files from %s", count, readme_dir)


def clean_output(output_dir: Path) -> None:
    """Clean the output directory (dist/)."""
    if output_dir.exists():
        count = 0
        for child in output_dir.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
            count += 1
        logger.info("Cleaned %d items from output directory %s", count, output_dir)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Created output directory %s", output_dir)
