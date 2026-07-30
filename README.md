# Global User Data Analysis

Global User Data Analysis is a product intelligence and social listening platform for mining real user needs, pain points, trend signals, and opportunity spaces from public discussions across global and regional communities.

The project is not limited to AI products. AI is one capability in the analysis and solution layer. The platform should help discover unmet demand across domains such as AI agents, developer tools, video creation, product sourcing, marketing, ecommerce, consumer apps, education, finance, games, productivity, and local services.

## Core Goal

Turn noisy public discussion into evidence-backed opportunity analysis:

- What people are trying to do
- Where current tools or workflows fail
- Which pain points repeat across platforms and personas
- Which problems show willingness to pay or urgent adoption signals
- Which products, categories, or workflows are gaining momentum
- Which concrete posts, comments, issues, and cases support the finding

## First Target Users

- Founders looking for product opportunities
- Product managers doing market and user research
- Investors scouting emerging categories
- Indie hackers validating ideas
- AI builders looking for high-leverage automation opportunities
- Marketing and growth teams tracking demand shifts

## First Theme Packs

1. AI agent tools: Codex, Claude Code, WorkBuddy, OpenClaw, Cursor, Devin-like tools, automation agents.
2. Creator workflows: video creation, shorts, thumbnails, scripts, editing, localization, game creation.
3. Ecommerce and sourcing: product selection, store operations, customer complaints, packaging, logistics, live commerce.
4. Marketing and growth: content distribution, ad creatives, SEO, social media operations, lead generation.
5. Developer and high-knowledge communities: GitHub, V2EX, Reddit, X, Hacker News, Zhihu, Bilibili, WeChat public articles.

## MVP Principle

Start with reliable, low-risk, high-signal sources before chasing every platform.

Recommended MVP source order:

1. GitHub issues/discussions/repos
2. V2EX topics/replies
3. Reddit subreddits via approved API or controlled pilot
4. X via paid API or third-party provider pilot
5. Bilibili public video comments/danmaku for creator/tool topics
6. WeChat public account articles and authorized account statistics where available
7. Xiaohongshu/Douyin only through official/authorized paths or low-volume manual research workflows

## Repository Structure

```text
.
├── README.md
├── docs/
│   ├── product-brief.md
│   ├── source-strategy.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── ai-analysis-pipeline.md
│   ├── mvp-roadmap.md
│   └── compliance-notes.md
└── .gitignore
```

## Current Status

MVP backend skeleton is implemented:

- FastAPI app with `/health`, `/ready`, source CRUD basics, source health tests, evidence/company search, rate policy management, topic pack/task creation, and collection task run endpoint.
- SQLite schema for sources, topic packs, tasks, runs, raw items, evidence items, company entities, market observations, geo entities, and session profiles.
- Local raw JSON store under `data/raw/...`.
- Connector base interface and working connectors:
  - `meta_search` backed by Tavily CLI.
  - `v2ex` backed by V2EX API 2.0 when a PAT is provided, with unauthenticated legacy latest-topic fallback.
  - `tianyan_ai` backed by the local `tyc` CLI, including `company_entities` enrichment.
  - `github` backed by GitHub REST search for repositories, issues, and releases.
  - `rss` backed by RSS/Atom public feeds with `feed:` and `keywords:` query support.
  - `hackernews` backed by Algolia HN search.
  - `baidu_search` backed by the local Baidu/Qianfan search skill when credentials are valid.
  - `stackexchange` backed by Stack Exchange API.
  - `npm` backed by npm registry search.
  - `dockerhub` backed by Docker Hub public search.
  - `devto` backed by DEV Community article API.
  - `gdelt` backed by GDELT Doc API, with rate-limit handling.
  - `huggingface` backed by Hugging Face Hub public model search; `HF_TOKEN` optional.
  - `arxiv` backed by the arXiv Atom API; no key required, but strict low cadence is needed.
- Source catalog endpoint `/source-catalog` tracks implemented, planned, and gated high-value sources from the strategy docs.
- CLI entrypoint `guda` with `init-db` and `demo-run`.

## Run Locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q

guda init-db
guda demo-run --connector meta_search --query 'semiconductor supply chain pain points China 2026' --limit 3
guda demo-run --connector v2ex --query 'node:programmer AI agent' --limit 3
guda demo-run --connector tianyan_ai --query '宁德时代新能源科技股份有限公司' --limit 1
uvicorn guda.api:app --host 127.0.0.1 --port 8000

curl 'http://127.0.0.1:8000/evidence/search?query=deployment&limit=5'
curl --get --data-urlencode 'query=宁德时代' 'http://127.0.0.1:8000/companies/search'
curl 'http://127.0.0.1:8000/source-catalog'
# Admin console uses relative paths and works behind path-based nginx proxying.
# Local: http://127.0.0.1:8000/admin/
```

Real connector smoke tests currently pass for GitHub, RSS, Hacker News, StackExchange, npm, Docker Hub, Dev.to, and Hugging Face. GDELT and arXiv are implemented but can return HTTP 429 and should be scheduled conservatively. Provider-scale sources such as SocialCrawl, TikHub, JustOneAPI, Xpoz, SociaVault, Apify, and Trends MCP are tracked in `/source-catalog` as key-gated adapters.

Runtime artifacts are ignored by git:

- `data/app.sqlite`
- `data/raw/`
- `.env`
