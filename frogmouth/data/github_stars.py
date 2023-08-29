"""Provides code for saving and loading bookmarks."""

from __future__ import annotations

from datetime import datetime
from json import JSONEncoder, dumps, loads
from pathlib import Path
from typing import Any, NamedTuple

from httpx import URL

from ..utility import is_likely_url
from .data_directory import data_directory


class GitHubStar(NamedTuple):
    """A GitHub Star."""

    title: str
    """The title of the bookmark."""
    location: Path | URL
    """The location of the bookmark."""
    date_starred: datetime
    """The date the repo was starred."""


def github_stars_file(username: str) -> Path:
    """Get the location of the bookmarks file.

    Returns:
        The location of the bookmarks file.
    """
    return data_directory() / "{username}_github_stars.json"


class GithubStarEncoder(JSONEncoder):
    """JSON encoder for the GitHub Star data."""

    def default(self, o: object) -> Any:
        """Handle the Path and URL values.

        Args:
            o: The object to handle.

        Return:
            The encoded object.
        """
        return str(o) if isinstance(o, (Path, URL)) else o


def save_bookmarks(bookmarks: list[GitHubStar]) -> None:
    """Save the given bookmarks.

    Args:
        bookmarks: The bookmarks to save.
    """
    github_stars_file().write_text(dumps(bookmarks, indent=4, cls=GithubStarEncoder))


def load_bookmarks() -> list[GitHubStar]:
    """Load the GitHub Stars.

    Returns:
        The bookmarks.
    """
    return (
        [
            GitHubStar(
                title,
                URL(location),
                date_starred,
            )
            for (title, location, date_starred) in loads(github_stars.read_text())
        ]
        if (github_stars := github_stars_file()).exists()
        else []
    )
