 # Starforge

Starforge is a data-driven strategy coach for indie devs and small teams who want to grow their GitHub stars fast. It inspects your public repositories, surfaces hidden momentum, and recommends high-leverage project ideas based on the freshest trends on GitHub.

## Why this matters

- **Practical** – Works with the public REST API. No LLMs or paid services required.
- **Frontier-aware** – Scans the newest repositories (e.g., created within the last 90 days) to detect hot topics/languages that are gaining stars right now.
- **Actionable** – Generates personalized playbooks: which repos to double down on, which languages to showcase, and concrete idea prompts you can ship next.

## Installation

```bash
pip install -e .
```

## Quickstart

```bash
export GITHUB_TOKEN=ghp_xxx   # optional but recommended for higher rate limits
starforge --user torvalds --limit 3
```

Sample output:

```
Profile pulse for torvalds
──────────────────────────
- Focus repos: linux (momentum 2.1), subsurface (momentum 1.4)
- Language leverage: C (82% of stars), C++ (12%)
- Fresh opportunities (last 90 days): AI infra, wasm build tools, GPU scheduling
- Idea drafts:
  • “GPU-native observability kit for C maintainers”
  • “WASM-first kernel playground with pluggable schedulers”
```

## CLI options

```
usage: starforge [-h] --user USER [--limit LIMIT] [--trend-lang TREND_LANG]
                 [--since-days SINCE_DAYS] [--save SAVE]
```

| Flag | Description |
|------|-------------|
| `--user` | GitHub username or org to analyze (required) |
| `--limit` | Number of high-momentum repos to highlight (default: 5) |
| `--trend-lang` | Force trending research for a specific language (default: auto) |
| `--since-days` | Window (days) for trending search (default: 90) |
| `--save` | Write the full JSON report to a path |

## How it works

1. **Profile ingestion** – Pulls all public repos (forks optional) and computes normalized metrics: velocity, star density, freshness, engagement.
2. **Signal synthesis** – Blends metrics into a transparent momentum score. We bias toward recent pushes and consistent growth rather than raw star count.
3. **Opportunity scan** – Uses the GitHub Search API to look for repos created within your window that already broke the star threshold. We cluster them by topic/language to infer momentum waves.
4. **Strategy modeling** – Matches your strongest languages against the hottest topics to output idea prompts and actionable moves.

## Roadmap ideas

- Add lightweight time-series persistence to detect deltas across runs.
- Build a `--post` flag to auto-create a GitHub Discussion or tweet with your action plan.
- Plug in open-source LLMs (e.g., `llama.cpp`) for richer prompt generation when desired.

## License

MIT

