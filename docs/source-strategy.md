# Source Strategy

## Principle

Coverage matters more than purity. The system should combine official APIs, paid data providers, open-source collectors, browser-assisted workflows, RSS/search feeds, and manual curation.

The goal is not to own every crawler. The goal is to maintain a reliable source registry and route each collection task to the best available acquisition path.

## Source Acquisition Modes

| Mode | Description | Best For | Risk / Cost |
|---|---|---|---|
| Official API | Platform-approved API with documented auth and limits | GitHub, YouTube, Douyin authorized accounts, WeChat official account stats | Stable but limited; approval needed |
| Paid data provider | Vendor provides social/search/ecommerce data APIs | X, Reddit, TikTok, Instagram, Xiaohongshu, app reviews, ecommerce reviews | Cost, vendor lock-in |
| Open-source connector | Community crawler/API wrapper/MCP server | Prototypes, long-tail sources, local-first experiments | Maintenance and compliance risk |
| Browser-assisted collection | Human-like logged-in browser or extension workflow | Semi-closed platforms, one-off research, manual source discovery | Lower scale; account risk if abused |
| Headless authenticated collection | Controlled Playwright/Chromium collection with stored session state | Sources where UI access is required and API/provider coverage is insufficient | Higher maintenance/compliance/account risk; must be explicit and budgeted |
| RSS / sitemap / search | Feeds and web search discovery | Blogs, news, newsletters, public pages | Incomplete but low risk |
| Manual import | CSV, saved URLs, screenshots, exported reports | Private research, paid reports, one-off analyst input | Human effort |

## Acquisition Ladder

Every important source should support a ranked acquisition ladder instead of a single hard-coded fetch method. The collector tries the safest, most stable layer first, then escalates only when coverage or access is insufficient.

Recommended ladder:

1. **Official API / authorized API**: documented endpoint, OAuth/API key, webhook, or export. This is the default for GitHub, YouTube, WeChat authorized stats, Douyin authorized account APIs, Tianyan AI, app stores, and provider APIs.
2. **Public unauthenticated endpoint**: public JSON/feed/page endpoint with light rate limits. Good for V2EX, Hacker News, RSS, selected Bilibili endpoints, and public static pages.
3. **Paid provider / MCP / data API**: use when direct access is expensive, restricted, or brittle. Good for X, Reddit at commercial scale, TikTok/Douyin, Xiaohongshu, Instagram, ecommerce reviews, app reviews, and broad social data.
4. **Logged-in browser session**: human-in-the-loop or browser-assisted access using a persisted session profile. Good for exploratory research, platform search, verifying provider samples, and semi-closed platforms.
5. **Headless authenticated collector**: controlled Playwright/Chromium automation with stored session state. Use only for explicitly approved sources/tasks when API/provider paths are inadequate.
6. **Manual import**: CSV/URL list/screenshots/exported reports for private research or high-risk platforms.

Escalation rules:

- Each source stores its ladder and current preferred layer.
- A task may cap the maximum allowed layer, e.g. `max_acquisition_layer=paid_provider` or `max_acquisition_layer=logged_in_browser`.
- Headless authenticated collection must be rate-limited, auditable, and disabled by default for broad recurring scans.
- Connector output should use the same raw JSON + normalized evidence schema regardless of acquisition layer.

## Build vs Buy vs Integrate

### Buy / Integrate First

Use paid or third-party providers when:

- Platform is restrictive or expensive to access directly.
- Coverage is more important than owning the crawler.
- The source is strategically important but not core engineering differentiation.
- Data quality and uptime are hard to maintain internally.

Candidate providers/tools to evaluate:

- Bright Data: social, ecommerce, business, finance, research data APIs and agent skills.
- ScrapeCreators: social media research skills and APIs for TikTok, Instagram, YouTube, Reddit, X, LinkedIn, Facebook, Threads, Bluesky, Pinterest.
- SociaVault: MCP and API for TikTok, Instagram, YouTube, X, LinkedIn, Facebook, Reddit, Threads, Twitch, Google, ad libraries.
- SocialCrawl / CreatorCrawl / Xpoz: social media APIs with MCP/SDK options.
- Apify: actor marketplace for many sources.
- JustOneAPI: broad China/global platform data API including Xiaohongshu, Douyin, Weibo, Bilibili, WeChat, Zhihu, ecommerce, Reddit, YouTube, Instagram.
- Enterprise listening suites: Brandwatch, Talkwalker, Meltwater, Sprinklr, Pulsar. Useful for benchmarking capabilities and possibly as upstream sources for enterprise pilots.

### Build Internally

Build first-party connectors when:

- Source has stable public APIs.
- Cost is low and limits are acceptable.
- Connector is core to the product's unique workflow.
- We need custom collection logic, evidence preservation, or citation control.

Good internal-first candidates:

- GitHub issues, discussions, repos, stars, releases.
- V2EX topics and replies.
- RSS/news/blog feeds.
- Hacker News.
- YouTube transcripts and comments where API quota allows.
- Bilibili comments/danmaku for limited public topics.

### Browser / Human-In-The-Loop

Use browser-assisted flows for:

- Xiaohongshu and Douyin exploratory research.
- WeChat article discovery and comment/context inspection.
- Platform search where API access is unavailable.
- Verifying paid-provider samples against live UI.

This should be rate-limited, auditable, and never designed as aggressive scraping.

## Initial Platform Matrix

| Platform | Priority | Suggested Path | Notes |
|---|---:|---|---|
| GitHub | P0 | Official API + webhooks + GraphQL | Best first source for developer pain points and project references |
| V2EX | P0 | Public API / lightweight scraper | High-signal China developer community |
| Reddit | P0 | Official API if approved, paid provider fallback | Commercial access/approval can be difficult |
| X / Twitter | P0 | Paid API or data provider | Expensive but critical for market/finance/AI narratives |
| Hacker News | P1 | Official Firebase/API + Algolia search | Good for startup/dev trends |
| YouTube | P1 | YouTube Data API + transcripts | Creator, education, product review signals |
| Bilibili | P1 | Public endpoints / provider / controlled crawler | Creator and China tech community signals |
| WeChat public accounts | P1 | Official authorized stats + article search/providers/manual | Comments require authorized article/account access |
| Xiaohongshu | P1 | Paid provider or browser-assisted research | Very valuable consumer/product data, high platform risk |
| Douyin | P1 | Official authorized account APIs + provider | Public trend coverage likely needs paid/provider path |
| Zhihu | P2 | Provider/browser/search | High-knowledge discussions; scraping risk |
| Weibo | P2 | Provider/public search/manual | Trend and public sentiment |
| Xueqiu | P2 | Provider/cookie-based controlled source | Finance and retail investor sentiment |
| News/RSS | P0 | RSS/search/news APIs | Needed for macro context, semiconductor, finance |
| Tianyan AI / Tianyancha | P0 | Official Tianyan AI CLI/Skill now configured | Authoritative China company, risk, equity, operations, IP, and industry discovery source |
| AxData / eltdx / TdxQuant A-share market data | P1 | AxData framework preferred; eltdx for TDX protocol/MCP research adapter; tdxquant-mcp for local logged-in TdxQuant terminal integration | China A-share quotes, K-line, tick/trade, auction, F10, topics, financials, sectors, formula execution, and optional dry-run trading tools; verify license and third-party data terms before production |
| Google Maps MCP | P1 | Official Google Maps API via MCP | Geocoding, reverse geocoding, place search/details, distance matrix, directions, elevation; useful for company address enrichment, store/POI/site selection, local-market context |
| App stores/review sites | P1 | Official/paid APIs | Strong product pain point signals |
| Ecommerce reviews | P1 | Paid provider | Product sourcing and consumer demand |

## Source Registry Fields

- `id`
- `name`
- `platform`
- `source_type`: official_api, paid_provider, browser, rss, search, manual, webhook
- `access_status`: active, pending_auth, blocked, paid_only, experimental, deprecated
- `acquisition_ladder`: ordered list of official_api, public_endpoint, paid_provider, logged_in_browser, headless_authenticated, manual
- `preferred_acquisition_layer`
- `max_allowed_acquisition_layer`
- `session_profile_id`: optional browser/session profile reference for logged-in collection
- `auth_profile_id`
- `base_url`
- `query_template`
- `rate_limit_policy`
- `allowed_content_types`
- `coverage_notes`
- `compliance_notes`
- `cost_model`
- `owner`
- `created_at`
- `updated_at`

## Collection Task Fields

- `id`
- `name`
- `topic_pack_id`
- `source_ids`
- `query`
- `keywords`
- `entities`
- `languages`
- `regions`
- `schedule`: cron or interval
- `lookback_window`
- `max_items_per_run`
- `budget_per_run`
- `dedupe_policy`
- `priority`
- `enabled`

## Topic Pack Examples

### Semiconductor Watch

Sources:

- Semiconductor news RSS/search
- Company press releases and filings
- Tianyan AI company discovery/enrichment for China semiconductor companies
- X accounts/lists
- Reddit/Hacker News/V2EX discussions
- GitHub repos/issues for EDA, CUDA, ML acceleration, chip toolchains
- Supply-chain blogs and job posts

Cadence:

- News/search: hourly
- Community discussions: 3-6 hours
- Deep synthesis: daily
- Weekly opportunity report

### Financial Markets Watch

Sources:

- X, Reddit, Xueqiu, financial news, filings, macro calendars
- Tianyan AI company enrichment for China-listed/private company checks
- AxData/eltdx/tdxquant-mcp for China A-share market structure, quotes, K-line, auction, F10, sectors, formulas, topics, and shortline indicators
- Google Maps MCP for company/venue geocoding, POI density, distance/time, and route context around markets, industrial parks, stores, and offices
- YouTube/Bilibili finance video transcripts/comments
- Polymarket and prediction markets where relevant

Cadence:

- Market-hours scan: 15-60 minutes
- Daily close report
- Weekly narrative shift report

### AI Agent Tools Watch

Sources:

- GitHub issues/discussions for Codex, Claude Code, OpenClaw, Cursor, WorkBuddy-like tools
- Reddit, X, Hacker News, V2EX
- YouTube/Bilibili reviews and comments
- Product changelogs and docs

Cadence:

- GitHub: hourly/daily depending repo velocity
- Social/search: 2-6 hours
- Weekly pain point map
