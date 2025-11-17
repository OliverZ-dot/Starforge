"""Repository analytics utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple


@dataclass
class RepoSnapshot:
    name: str
    full_name: str
    stars: int
    forks: int
    watchers: int
    open_issues: int
    language: str | None
    topics: Tuple[str, ...]
    pushed_at: datetime
    created_at: datetime
    description: str | None
    url: str

    @property
    def days_since_push(self) -> float:
        return max((datetime.now(timezone.utc) - self.pushed_at).total_seconds() / 86400, 0.01)

    @property
    def age_days(self) -> float:
        return max((datetime.now(timezone.utc) - self.created_at).total_seconds() / 86400, 0.01)

    def momentum(self) -> float:
        freshness_factor = max(0.2, 1.5 - (self.days_since_push / 60))
        maturity_factor = min(1.2, 0.6 + (365 / self.age_days))
        star_density = self.stars / (self.age_days ** 0.5)
        engagement = 1 + ((self.forks + self.watchers + self.open_issues * 0.2) / 100)
        return round(star_density * freshness_factor * maturity_factor * engagement, 2)


@dataclass
class ProfilePulse:
    username: str
    repo_count: int
    total_stars: int
    languages: Dict[str, int]
    top_repos: List[RepoSnapshot]


def parse_repo(repo_payload: Dict) -> RepoSnapshot:
    def _parse_ts(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    topics = tuple(repo_payload.get("topics") or ())
    return RepoSnapshot(
        name=repo_payload["name"],
        full_name=repo_payload["full_name"],
        stars=repo_payload.get("stargazers_count", 0),
        forks=repo_payload.get("forks_count", 0),
        watchers=repo_payload.get("subscribers_count", repo_payload.get("watchers_count", 0)),
        open_issues=repo_payload.get("open_issues_count", 0),
        language=repo_payload.get("language"),
        topics=topics,
        pushed_at=_parse_ts(repo_payload["pushed_at"]),
        created_at=_parse_ts(repo_payload["created_at"]),
        description=repo_payload.get("description"),
        url=repo_payload.get("html_url"),
    )


def summarize_profile(username: str, repos: Iterable[RepoSnapshot], top_n: int = 5) -> ProfilePulse:
    repo_list = list(repos)
    languages: Dict[str, int] = {}
    total_stars = 0
    for repo in repo_list:
        total_stars += repo.stars
        if repo.language:
            languages[repo.language] = languages.get(repo.language, 0) + repo.stars
    top_repos = sorted(repo_list, key=lambda r: r.momentum(), reverse=True)[:top_n]
    return ProfilePulse(
        username=username,
        repo_count=len(repo_list),
        total_stars=total_stars,
        languages=languages,
        top_repos=top_repos,
    )

