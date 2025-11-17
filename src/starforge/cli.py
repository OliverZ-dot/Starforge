"""Command-line interface for Starforge."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .analysis import RepoSnapshot, parse_repo, summarize_profile
from .github_api import GitHubClient, GitHubError
from .strategies import (
    TrendInsight,
    build_action_prompts,
    default_trend_window,
    select_focus_repos,
    summarize_languages,
)

console = Console()


def fetch_trending_opportunities(
    client: GitHubClient,
    languages: Iterable[str | None],
    days_back: int,
    per_language: int = 5,
) -> List[TrendInsight]:
    cutoff = default_trend_window(days_back)
    insights: List[TrendInsight] = []
    for language in languages:
        query_bits = [f"created:>={cutoff}", "stars:>50"]
        if language:
            query_bits.append(f"language:{language}")
        query = " ".join(query_bits)
        payload = client.search_repositories(query=query, per_page=per_language)
        for item in payload.get("items", []):
            topic = (item.get("topics") or [item.get("name")])[0]
            insights.append(
                TrendInsight(
                    topic=topic.replace("-", " ").title(),
                    language=item.get("language") or language,
                    stars=item.get("stargazers_count", 0),
                    description=item.get("description") or "",
                    repo_url=item.get("html_url"),
                )
            )
    return sorted(insights, key=lambda t: t.stars, reverse=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Grow your GitHub stars with data.")
    parser.add_argument("--user", required=True, help="GitHub username or organization")
    parser.add_argument("--limit", type=int, default=5, help="Number of focus repos to highlight")
    parser.add_argument(
        "--include-forks",
        action="store_true",
        help="Include forked repositories in the analysis",
    )
    parser.add_argument(
        "--trend-lang",
        dest="trend_lang",
        help="Force trending research for a specific language",
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=90,
        help="Trend search window in days (default: 90)",
    )
    parser.add_argument("--save", help="Optional path to save the JSON report")
    return parser


def render_focus_table(repos: List[RepoSnapshot]) -> Table:
    table = Table(title="High-momentum repos", show_lines=True)
    table.add_column("Repo")
    table.add_column("Momentum", justify="right")
    table.add_column("Stars", justify="right")
    table.add_column("Language")
    table.add_column("Last Push (days)")
    for repo in repos:
        table.add_row(
            repo.full_name,
            f"{repo.momentum():.2f}",
            str(repo.stars),
            repo.language or "mixed",
            f"{repo.days_since_push:.1f}",
        )
    return table


def render_trend_table(trends: List[TrendInsight]) -> Table:
    table = Table(title="Fresh opportunities", show_lines=True)
    table.add_column("Topic")
    table.add_column("Language")
    table.add_column("Stars", justify="right")
    table.add_column("Repository")
    for trend in trends[:5]:
        table.add_row(trend.topic, trend.language or "mixed", str(trend.stars), trend.repo_url)
    return table


def save_report(path: str, payload: dict) -> None:
    target = Path(path)
    target.write_text(json.dumps(payload, indent=2))
    console.print(f"[green]Saved report to {target}[/green]")


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    client = GitHubClient()
    try:
        raw_repos = client.get_user_repos(args.user, include_forks=args.include_forks)
    except GitHubError as exc:
        console.print(f"[red]Failed to fetch repositories: {exc}[/red]")
        raise SystemExit(1)

    snapshots = [parse_repo(repo) for repo in raw_repos]
    if not snapshots:
        console.print("[yellow]No repositories found. Try --include-forks or another user.[/yellow]")
        raise SystemExit(0)

    pulse = summarize_profile(args.user, snapshots, top_n=args.limit)
    focus_repos = select_focus_repos(pulse.top_repos, args.limit)
    lang_targets = [args.trend_lang] if args.trend_lang else [lang for lang, _ in summarize_languages(pulse)]
    if not lang_targets:
        lang_targets = [None]
    trends = fetch_trending_opportunities(client, lang_targets, args.since_days)
    prompts = build_action_prompts(pulse, trends, limit=3)

    console.rule(f"Profile pulse for {args.user}")
    console.print(render_focus_table(focus_repos))
    console.print(render_trend_table(trends))
    console.print(Panel("\n".join(f"• {idea}" for idea in prompts), title="Idea prompts"))

    report = {
        "username": args.user,
        "focus_repos": [
            {
                "name": repo.full_name,
                "momentum": repo.momentum(),
                "stars": repo.stars,
                "language": repo.language,
                "topics": repo.topics,
                "url": repo.url,
            }
            for repo in focus_repos
        ],
        "languages": pulse.languages,
        "trends": [trend.__dict__ for trend in trends],
        "idea_prompts": prompts,
    }

    if args.save:
        save_report(args.save, report)


if __name__ == "__main__":
    main()

