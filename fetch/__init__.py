"""Data fetching layer for Developer Atlas."""

from fetch.base import BaseFetcher
from fetch.github import GitHubFetcher

__all__ = ["BaseFetcher", "GitHubFetcher"]
