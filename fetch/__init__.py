"""Data fetching layer for Developer Atlas."""

from fetch.base import BaseFetcher
from fetch.github import GitHubFetcher
from fetch.remote import RemoteFetcher

__all__ = ["BaseFetcher", "GitHubFetcher", "RemoteFetcher"]
