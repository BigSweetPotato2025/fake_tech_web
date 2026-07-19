"""Deployment utilities for Developer Atlas."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def deploy_rsync(
    local_dist: Path,
    remote_host: str,
    remote_path: str,
    delete: bool = True,
) -> bool:
    """Deploy the dist/ directory to a remote server via rsync."""
    if not local_dist.exists():
        logger.error("Local dist directory not found: %s", local_dist)
        return False

    cmd = ["rsync", "-avz", "--checksum"]
    if delete:
        cmd.append("--delete")
    cmd.extend([f"{local_dist}/", f"{remote_host}:{remote_path}"])

    try:
        logger.info("Deploying to %s:%s", remote_host, remote_path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            logger.info("Deployment successful")
            return True
        else:
            logger.error("rsync failed (exit %d): %s", result.returncode, result.stderr)
            return False
    except subprocess.TimeoutExpired:
        logger.error("rsync timed out")
        return False
    except FileNotFoundError:
        logger.error("rsync not found")
        return False


def deploy_git(dist_dir: Path, repo_dir: Path) -> bool:
    """Copy dist/ contents to a git repository for git-based deployment."""
    if not dist_dir.exists():
        logger.error("Dist directory not found: %s", dist_dir)
        return False
    if not (repo_dir / ".git").exists():
        logger.error("Not a git repository: %s", repo_dir)
        return False

    try:
        for child in repo_dir.iterdir():
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        for child in dist_dir.iterdir():
            dest = repo_dir / child.name
            if child.is_dir():
                shutil.copytree(child, dest, symlinks=True)
            else:
                shutil.copy2(child, dest)
        logger.info("Copied dist/ to %s", repo_dir)
        return True
    except OSError as e:
        logger.error("Failed to copy to git repo: %s", e)
        return False
