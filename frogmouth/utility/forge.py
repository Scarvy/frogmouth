"""Code for getting files from a forge."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List
from httpx import URL, AsyncClient, HTTPStatusError, RequestError

from .advertising import USER_AGENT


async def build_raw_forge_url(
    url_format: str,
    owner: str,
    repository: str,
    branch: str | None = None,
    desired_file: str | None = None,
) -> URL | None:
    """Attempt to get raw forge URL for the given file.

    Args:
        owner: The owner of the repository to look in.
        repository: The repository to look in.
        branch: The optional branch to look in.
        desired_file: Optional name of the file to go looking for.

    Returns:
        The URL for the file, or `None` if none could be guessed.

    If the branch isn't supplied then `main` and `master` will be tested.

    If the target file isn't supplied it's assumed that `README.md` is the
    target.
    """
    desired_file = desired_file or "README.md"
    async with AsyncClient() as client:
        for test_branch in (branch,) if branch else ("main", "master"):
            url = url_format.format(
                owner=owner,
                repository=repository,
                branch=test_branch,
                file=desired_file,
            )
            try:
                response = await client.head(
                    url,
                    follow_redirects=True,
                    headers={"user-agent": USER_AGENT},
                )
            except RequestError:
                # We've failed to even make the request, there's no point in
                # trying to build anything here.
                return None
            try:
                response.raise_for_status()
                return URL(url)
            except HTTPStatusError:
                pass
    return None


async def build_raw_github_url(
    owner: str,
    repository: str,
    branch: str | None = None,
    desired_file: str | None = None,
) -> URL | None:
    """Attempt to get the GitHub raw URL for the given file.

    Args:
        owner: The owner of the repository to look in.
        repository: The repository to look in.
        branch: The optional branch to look in.
        desired_file: Optional name of the file to go looking for.

    Returns:
        The URL for the file, or `None` if none could be guessed.

    If the branch isn't supplied then `main` and `master` will be tested.

    If the target file isn't supplied it's assumed that `README.md` is the
    target.
    """
    return await build_raw_forge_url(
        "https://raw.githubusercontent.com/{owner}/{repository}/{branch}/{file}",
        owner,
        repository,
        branch,
        desired_file,
    )


async def build_raw_gitlab_url(
    owner: str,
    repository: str,
    branch: str | None = None,
    desired_file: str | None = None,
) -> URL | None:
    """Attempt to get the GitLab raw URL for the given file.

    Args:
        owner: The owner of the repository to look in.
        repository: The repository to look in.
        branch: The optional branch to look in.
        desired_file: Optional name of the file to go looking for.

    Returns:
        The URL for the file, or `None` if none could be guessed.

    If the branch isn't supplied then `main` and `master` will be tested.

    If the target file isn't supplied it's assumed that `README.md` is the
    target.
    """
    return await build_raw_forge_url(
        "https://gitlab.com/{owner}/{repository}/-/raw/{branch}/{file}",
        owner,
        repository,
        branch,
        desired_file,
    )


async def build_raw_bitbucket_url(
    owner: str,
    repository: str,
    branch: str | None = None,
    desired_file: str | None = None,
) -> URL | None:
    """Attempt to get the BitBucket raw URL for the given file.

    Args:
        owner: The owner of the repository to look in.
        repository: The repository to look in.
        branch: The optional branch to look in.
        desired_file: Optional name of the file to go looking for.

    Returns:
        The URL for the file, or `None` if none could be guessed.

    If the branch isn't supplied then `main` and `master` will be tested.

    If the target file isn't supplied it's assumed that `README.md` is the
    target.
    """
    return await build_raw_forge_url(
        "https://bitbucket.org/{owner}/{repository}/raw/{branch}/{file}",
        owner,
        repository,
        branch,
        desired_file,
    )


async def build_raw_codeberg_url(
    owner: str,
    repository: str,
    branch: str | None = None,
    desired_file: str | None = None,
) -> URL | None:
    """Attempt to get the Codeberg raw URL for the given file.

    Args:
        owner: The owner of the repository to look in.
        repository: The repository to look in.
        branch: The optional branch to look in.
        desired_file: Optional name of the file to go looking for.

    Returns:
        The URL for the file, or `None` if none could be guessed.

    If the branch isn't supplied then `main` and `master` will be tested.

    If the target file isn't supplied it's assumed that `README.md` is the
    target.
    """
    return await build_raw_forge_url(
        "https://codeberg.org/{owner}/{repository}/raw//branch/{branch}/{file}",
        owner,
        repository,
        branch,
        desired_file,
    )


async def _import_github_repo_details(username, total_repos=None):
    """Fetches repository details of starred repositories for a given GitHub user.

    Args:
        username (str): GitHub account username.
        total_repos (int, optional): The maximum number of repositories to fetch details for.

    Returns:
        List[dict] | None: A list of dictionaries containing repository details
        (owner, repo_name, starred_at), or None if the request fails or no repositories are found.
    """
    repo_details = []

    next_page_of_results = f"https://api.github.com/users/{username}/starred"

    async with AsyncClient() as client:
        while next_page_of_results:
            try:
                response = await client.get(
                    next_page_of_results,
                    headers={"Accept": "application/vnd.github.v3.star+json"},
                )

                next_page_of_results = response.links.get("next", {}).get("url")

                response.raise_for_status()
                stars_response = response.json()

                for repo_info in stars_response:
                    repo = repo_info["repo"]

                    timestamp = datetime.strptime(
                        repo_info["starred_at"], "%Y-%m-%dT%H:%M:%SZ"
                    )

                    details = {
                        "owner": repo["owner"]["login"],
                        "repo_name": repo["name"],
                        "starred_at": timestamp,
                    }
                    repo_details.append(details)

                    if total_repos is not None and len(repo_details) >= total_repos:
                        break  # Stop if we have fetched the desired number of repositories

                if total_repos is not None and len(repo_details) >= total_repos:
                    break  # Stop if we have fetched the desired number of repositories

            except (RequestError, HTTPStatusError):
                # Handle request errors or HTTP status errors here
                return None

    return repo_details


async def import_github_stars(username, total_repos=None) -> List[URL]:
    """Fetches GitHub raw URLs of starred repositories for a given GitHub user.

    Args:
        username (str): GitHub account username.
        total_repos (int, optional): The maximum number of repositories to fetch URLs for.

    Returns:
        List[URL]: A list of GitHub raw URLs for the starred repositories.
    """
    repo_details = await _import_github_repo_details(username, total_repos)

    build_tasks = [
        build_raw_github_url(repo["owner"], repo["repo_name"]) for repo in repo_details
    ]
    urls = await asyncio.gather(*build_tasks)

    return urls
