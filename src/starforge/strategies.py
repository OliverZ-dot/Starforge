"""Strategy modeling utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Sequence

from .analysis import ProfilePulse, RepoSnapshot


@dataclass
class TrendInsight:
    topic: str
    language: str | None
    stars: int
    description: str
    repo_url: str


def select_focus_repos(repos: Sequence[RepoSnapshot], limit: int) -> List[RepoSnapshot]:
    return sorted(repos, key=lambda r: r.momentum(), reverse=True)[:limit]


def summarize_languages(pulse: ProfilePulse, limit: int = 3) -> List[tuple[str, int]]:
    return sorted(pulse.languages.items(), key=lambda kv: kv[1], reverse=True)[:limit]


def build_action_prompts(
    pulse: ProfilePulse,
    trends: Iterable[TrendInsight],
    limit: int = 3,
) -> List[str]:
    ideas: List[str] = []
    trend_list = list(trends)
    top_langs = summarize_languages(pulse, limit=limit)
    for idx, trend in enumerate(trend_list[:limit]):
        lang = trend.language or (top_langs[idx][0] if idx < len(top_langs) else "Python")
        repo_name = pulse.top_repos[idx].name if idx < len(pulse.top_repos) else "flagship"
        idea = (
            f"Build a {trend.topic} toolkit in {lang} that plugs directly into {repo_name}; "
            f"mirror what {trend.repo_url} is doing but tailor it for your audience."
        )
        ideas.append(idea)
    if not ideas:
        ideas.append("Ship a public roadmap issue outlining the next 3 high-impact milestones.")
    return ideas


def default_trend_window(days_back: int) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    return cutoff.strftime("%Y-%m-%d")

