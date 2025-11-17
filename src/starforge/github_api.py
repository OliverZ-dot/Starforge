"""Thin GitHub REST API client tailored for Starforge."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import requests

API_ROOT = "https://api.github.com"
PREVIEW_HEADERS = {
    "Accept": "application/vnd.github+json, application/vnd.github.mercy-preview+json"
}


class GitHubError(RuntimeError):
    """Raised when the GitHub API returns an unexpected response."""


@dataclass
class RateLimitInfo:
    remaining: Optional[int]
    reset_epoch: Optional[int]

    def pretty_reset(self) -> str:
        if not self.reset_epoch:
            return "unknown"
        delta = max(0, int(self.reset_epoch - time.time()))
        minutes, seconds = divmod(delta, 60)
        return f"{minutes}m{seconds:02d}s"


class GitHubClient:
    def __init__(self, token: Optional[str] = None, session: Optional[requests.Session] = None) -> None:
        self._token = token or os.getenv("GITHUB_TOKEN")
        self._session = session or requests.Session()

    def _headers(self) -> Dict[str, str]:
        headers = dict(PREVIEW_HEADERS)
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = path if path.startswith("http") else f"{API_ROOT}{path}"
        response = self._session.request(method, url, headers=self._headers(), timeout=30, **kwargs)
        if response.status_code >= 400:
            raise GitHubError(
                f"GitHub API error {response.status_code}: {response.text}"
            )
        return response

    @staticmethod
    def _parse_rate_limit(response: requests.Response) -> RateLimitInfo:
        remaining = response.headers.get("x-ratelimit-remaining")
        reset = response.headers.get("x-ratelimit-reset")
        return RateLimitInfo(
            remaining=int(remaining) if remaining is not None else None,
            reset_epoch=int(reset) if reset is not None else None,
        )

    def get_user_repos(
        self,
        username: str,
        include_forks: bool = False,
        visibility: str = "public",
    ) -> List[Dict[str, Any]]:
        """Return repositories for `username`."""
        repos: List[Dict[str, Any]] = []
        page = 1
        while True:
            params = {
                "type": visibility,
                "sort": "pushed",
                "per_page": 100,
                "page": page,
            }
            response = self._request("GET", f"/users/{username}/repos", params=params)
            chunk = response.json()
            if not chunk:
                break
            for repo in chunk:
                if not include_forks and repo.get("fork"):
                    continue
                repos.append(repo)
            page += 1
        return repos

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
    ) -> Dict[str, Any]:
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
        }
        response = self._request("GET", "/search/repositories", params=params)
        return response.json()

    def fetch_topics(self, full_name: str) -> Iterable[str]:
        response = self._request("GET", f"/repos/{full_name}/topics")
        data = response.json()
        return data.get("names", [])

