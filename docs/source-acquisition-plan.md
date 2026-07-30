# Source Acquisition Plan

This document consolidates concrete source acquisition research for the Global User Data Analysis project.

## Acquisition Ladder

Every source should define a ranked acquisition ladder:

1. `official_api`: documented and authorized platform/provider API.
2. `public_endpoint`: public unauthenticated endpoint, RSS, sitemap, or static page.
3. `paid_provider`: paid data API, MCP server, hosted actor, or licensed dataset.
4. `logged_in_browser`: persisted browser session for exploratory/manual collection.
5. `headless_authenticated`: controlled Playwright/Chromium collector with persisted session state.
6. `manual`: CSV, URL list, screenshots, exported reports.

The collector should start from the safest layer and escalate only when task configuration allows it. The normalized evidence schema is the same regardless of acquisition layer.

## MVP Connector Order

### P0 Build Directly

| Connector | Why | Acquisition layer | Notes |
|---|---|---|---|
| GitHub | Highest-signal developer/product pain source | official_api | REST + GraphQL + webhooks; issues, discussions, comments, releases, repos |
| RSS / News / Blogs | Low-risk trend and context source | public_endpoint | feedparser + search/Tavily/Baidu/AnySearch discovery |
| V2EX | High-signal China developer community | official_api | API 2.0, PAT, about 600 req/hour/IP default |
| Hacker News | Startup/developer trend source | public_endpoint | Firebase API + Algolia HN Search |
| Meta Search | Cross-provider source discovery | official_api / paid_provider | web_search + Tavily + AnySearch + Baidu Search |
| Tianyan AI | Authoritative China company enrichment | official_api | Existing `tyc` CLI/Skill integration |

### P1 Integrate / Buy Early

| Connector | Why | Acquisition layer | Notes |
|---|---|---|---|
| Reddit | Strategic global discussion source | official_api or paid_provider | Official API requires OAuth and commercial approval/terms review; provider fallback likely needed |
| X / Twitter | Critical for AI/finance/market narratives | paid_provider or official_api | Cost and access are the main constraint |
| YouTube | Creator/video/product review signal | official_api | Data API quota; comments/video metadata first, transcripts when available/authorized |
| Bilibili | China creator/tech comments and danmaku | public_endpoint / paid_provider / logged_in_browser | Narrow pilot first; provider for scale |
| WeChat public accounts | China high-knowledge/business content | official_api for owned accounts; paid_provider/manual for arbitrary accounts | Comments/stats constrained to authorized accounts/articles |
| Xiaohongshu | Consumer/product demand | paid_provider / logged_in_browser | Provider first; browser only for validation/sample collection |
| Douyin | China short video/public trends | official_api for authorized accounts; paid_provider for public search | Public listening likely provider-based |
| App/review stores | Product pain points | official_api for owned apps; paid_provider for competitor coverage | Apple/Google official APIs mainly owned-app oriented |
| AxData / eltdx / tdxquant-mcp | A-share market data and financial context | public_endpoint / official_api / MCP / logged_in_browser | Prefer AxData as framework; eltdx is TDX protocol/MCP research adapter; tdxquant-mcp requires local logged-in TdxQuant terminal and `TQ_PATH`; disable real trading by default |
| Google Maps MCP | Geocoding, POI, distance/time, route, elevation, place details | official_api / MCP | Needs Google Maps API key; use for company address enrichment, store/site research, industrial park geography, routing/accessibility context |
| Paid provider abstraction | Coverage accelerator | paid_provider | Start with 1-2 providers after sample validation |

### P2 Defer / Provider-Only Initially

| Connector | Why | Acquisition layer | Notes |
|---|---|---|---|
| Stack Exchange | Developer Q&A signal | official_api | Useful, but lower priority than GitHub/V2EX/HN |
| Zhihu | China high-knowledge discussion | paid_provider / logged_in_browser | Avoid broad unofficial scraping |
| Weibo | Public sentiment/trends | paid_provider / logged_in_browser | API limits/login walls |
| Xueqiu | Finance sentiment | logged_in_browser / paid_provider | Useful for finance packs, but session/licensing risk |
| npm/PyPI/Docker Hub/Dev.to | Developer ecosystem trend proxies | public_endpoint / official_api | Add after core social/news sources |

## Global / Technical Sources

### GitHub

- Path: official REST + GraphQL + webhooks.
- Auth: PAT or GitHub App. REST unauthenticated rate around 60/hour; authenticated around 5,000/hour; search has separate limits.
- Collect: repo metadata, stars/forks, issues, PRs, comments, labels, reactions, discussions, releases, timestamps, author hashes, URLs.
- Cadence: high-velocity watched repos hourly; long-tail daily; webhooks where configured.
- Connector: `GitHubConnector` with REST search, GraphQL hydration, ETag support, cursor by `updated_at`, and webhook ingestion.
- Priority: P0.

### Reddit

- Path: official API for approved use; paid provider for production-scale/commercial monitoring.
- Auth: OAuth. Commercial/data/AI use needs terms review or commercial agreement/provider.
- Collect: posts, comments, subreddit, author hash, score, upvote ratio if available, flair, permalink, created time.
- Cadence: topic/subreddit search every 2-6h; high-priority hot/new 30-60m only with licensing/budget.
- Connector: `RedditConnector` or `ProviderConnector` with cursor by post/comment ID and time.
- Priority: P0 strategically, but gated.

### Hacker News

- Path: Firebase API + Algolia HN Search API.
- Auth: none.
- Collect: stories, comments, Ask HN, Show HN, jobs, title, text, URL, author hash, score, descendants, parent/child IDs, timestamps.
- Cadence: front/new/Ask/Show every 15-60m; keyword backfill every 3-6h.
- Priority: P0/P1.

### Stack Overflow / Stack Exchange

- Path: official Stack Exchange API v2.3.
- Auth: app key recommended; OAuth only for user/private/write flows.
- Collect: questions, answers, comments, tags, score, views, accepted answer, owner hash, creation/update dates, links, bodies via custom filters.
- Cadence: tag/keyword scans hourly to daily; honor `backoff`.
- Priority: P2/P1.

### YouTube

- Path: YouTube Data API v3 for metadata/comments; transcripts only where available and allowed.
- Auth: Google Cloud API key/OAuth. Default quota is limited; `search.list` is expensive compared with `videos.list` and `commentThreads.list`.
- Collect: video metadata, channel, title, description, stats, comments, replies, published time, transcripts when available.
- Cadence: watched channels hourly/daily; comments daily; broad search sparingly.
- Priority: P1.

### X / Twitter

- Path: official paid API or paid social provider.
- Auth/cost: developer account and paid access/credits; broad listening is expensive.
- Collect: posts, replies, quotes, repost relationships, public metrics, user/profile fields, lists/trends where available.
- Cadence: AI/finance narratives 15-60m with budget; otherwise 2-6h sampled scans.
- Priority: P0 strategically, paid/provider-first.

### RSS / News / Blogs

- Path: RSS/Atom/JSON Feed, GDELT, NewsAPI, Tavily/Baidu/AnySearch discovery.
- Auth: RSS none; paid news APIs as configured.
- Collect: title, link, summary/content, author, source, published/updated time, tags, canonical URL.
- Cadence: hourly for macro/semiconductor/finance; daily for blogs.
- Priority: P0.

### App Stores / Review Sites

- Path: official APIs for owned apps; providers for competitor market coverage.
- Auth: Apple App Store Connect JWT, Google Play service account/OAuth, or paid provider key.
- Collect: reviews, ratings, title/body, locale/country, app version, rank/category, keyword/app metadata.
- Cadence: owned reviews hourly/daily; competitor reviews daily.
- Priority: P1.

## China / Community / Media Sources

### V2EX

- Path: official API 2.0.
- Auth: Personal Access Token, `Authorization: Bearer ...`.
- Endpoints: `https://www.v2ex.com/api/v2/`, `nodes/:node_name/topics`, `topics/:topic_id`, `topics/:topic_id/replies`.
- Collect: topic id/title/content/url/node/member/replies/created; replies text/author/time.
- Cadence: 1-6h by node.
- Priority: P0.

### Bilibili

- Path: public endpoints for narrow pilot; paid provider for scale; browser/session validation when needed.
- Providers/references: JustOneAPI, TikHub, bilibili-API-collect, MediaCrawler as schema reference.
- Collect: video title, BVID/AID/CID, UP, publish time, stats, comments, replies, danmaku, captions/transcripts where available.
- Cadence: topic scans 2-6h; creator sync daily.
- Risk: medium; endpoint/signature drift and rate limits.
- Priority: P1, with narrow P0 pilot if easy.

### WeChat Public Accounts

- Path: official API for owned/authorized accounts; provider/manual/browser for arbitrary public account discovery.
- Official scope: article analytics, comments for authorized content.
- Collect: article title/body/html/url/account/author/publish time/read count/like/comment count/comments/replies where allowed.
- Cadence: authorized stats daily; provider/search campaigns 2-6h.
- Risk: high for arbitrary accounts/comments.
- Priority: P1.

### Xiaohongshu

- Path: paid provider first; logged-in browser for sample validation; headless only if explicitly allowed for a narrow task.
- Providers/references: TikHub, JustOneAPI, MediaCrawler as schema reference.
- Collect: note id/title/body/images/video/author/tags/location/publish time/likes/collects/comments/shares/replies/product tags.
- Cadence: 6-24h topic/product scans.
- Risk: high; restrictive platform.
- Priority: P1.

### Douyin

- Path: official authorized account APIs for owned/authorized content; paid provider for public search/trends.
- Auth: Douyin Open Platform app + user OAuth scopes for videos/comments/stats.
- Collect: video id/title/share URL/cover/create time/status/play/digg/comment/share stats/comments/replies.
- Cadence: authorized account hourly/daily; public provider 2-6h.
- Priority: P1.

### Zhihu / Weibo / Xueqiu

- Path: paid provider or logged-in browser/manual for low-volume research.
- Collect: question/answer/article/post/comment text, author hash, engagement, publish/update time, stock/topic symbols where applicable.
- Cadence: daily/weekly, or finance market-hours for Xueqiu if approved.
- Risk: higher due to session/platform restrictions and finance data licensing.
- Priority: P2 initially.

### Baidu Search / Baidu Baike

- Path: installed `baidu-search` skill using Qianfan/Baidu API key.
- Env: `BAIDU_SEARCH_API_KEY` or `QIANFAN_API_KEY`.
- Collect: query, title, snippet, URL, rank, source domain, Baike entity summary.
- Cadence: hourly/daily depending topic.
- Priority: P0 for Chinese discovery.

### Tianyan AI / Tianyancha

- Path: installed `tyc` CLI + `tyc-it` skill.
- Use: authoritative company/entity enrichment, not broad social listening.
- Collect: company identity, registration, legal rep, industry, shareholders, risk, litigation, penalties, IP, bids, recruitment.
- Cadence: on-demand enrichment; daily/weekly entity list enrichment.
- Priority: P0.

### AxData / eltdx / tdxquant-mcp A-share Market Data

- Path: prefer AxData as the broader Apache-2.0 local quantitative database framework; use eltdx as the focused TDX protocol/MCP research adapter; use tdxquant-mcp when a local logged-in TdxQuant/通达信 terminal is available and terminal-side strategy APIs are needed.
- Sources covered:
  - eltdx: 通达信 7709 行情、7615 F10、行情快照、K 线、分时、逐笔/成交明细、集合竞价、代码表、财务基础、股本变迁、题材/概念、公告、新闻、研报、估值、短线指标。
  - AxData: 通达信、交易所、巨潮、腾讯财经、新浪财经、东方财富、财联社、开盘红等公开源接口；local Parquet data layer; plugin system; local API/Web.
  - tdxquant-mcp: local TdxQuant `tqcenter.py` MCP wrapper with K-line/tick/snapshot/subscription, stock info, sectors, financial reports, convertible bonds/new stocks, trading calendar, formula execution, cache refresh, custom sectors, and trading account/order/position tools.
- Acquisition layer: `public_endpoint` / `official_api` / `MCP` / `logged_in_browser`; tdxquant-mcp requires a local logged-in TdxQuant/通达信 terminal, `TQ_PATH`, and possibly `TQ_DLL_PATH`.
- MCP tools:
  - eltdx: `eltdx_quote`, `eltdx_kline`, `eltdx_stock_profile`, `eltdx_stock_topics`, `eltdx_topic_stocks`, `eltdx_company_profile`, `eltdx_hot_topics`, `eltdx_auction_0925`.
  - tdxquant-mcp: `tools_catalog`, `market_get_kline`, `market_get_snapshot`, `market_subscribe_hq`, `stock_get_info`, `stock_get_more_info`, `stock_get_capital_info`, `sector_list`, `sector_stocks`, `financial_get_report_range`, `financial_get_report_by_date`, `calendar_get_trading_calendar`, `utility_formula_run`, and trade tools such as `trade_order_stock` / `trade_cancel_order_stock`.
- Collect: quote snapshots, OHLCV bars, minute series, trade ticks, auction points, F10/company profile, concepts/topics/sectors, topic constituents, finance basics, valuation, formula results, shortline indicators such as open turnover, auction/previous-day ratio, seal/float ratio, limit-board text.
- Cadence: quote/minute/tick during China market hours only when a finance topic pack requires it; K-line/F10/topics daily; enrichment on demand for mentioned A-share companies.
- Connector design: `AshareMarketDataConnector` writes raw JSON per API/MCP response and normalizes into a separate `market_observations`/`company_entities` layer rather than treating price bars as user evidence.
- Safety: trading tools must be excluded from collection adapters or forced to `dry_run=true`; real order/cancel operations are outside this product's data-collection scope.
- Compliance: AxData code is Apache-2.0, but third-party data rights remain with source providers. eltdx uses a Research-Only license and explicitly forbids commercial, paid, production, resale, market-data vending, and automated trading service usage. tdxquant-mcp currently has no clear repository license in the sources checked; treat it as evaluation-only until licensing and TdxQuant/通达信 data terms are resolved.
- Priority: P1 for Financial Markets Watch and China semiconductor/company context.

### Google Maps MCP

- Path: official Google Maps API through the Google Maps MCP server.
- Auth: `GOOGLE_MAPS_API_KEY` or equivalent Google Maps Platform API key; billing/quota must be configured in Google Cloud.
- Capabilities: geocoding, reverse geocoding, place search, place details, distance matrix, directions, and elevation.
- Collect: normalized address, latitude/longitude, place id, place name/type, ratings/reviews metadata when available, opening hours, contact fields when available, distance/time between origins and destinations, route summaries, elevation.
- Use cases: enrich company addresses from Tianyan/filings; analyze store/venue/industrial park geography; estimate commute/logistics accessibility; find nearby competitors/POIs; add location context to local consumer demand or offline retail topics.
- Cadence: on-demand enrichment or daily batch for new/changed entities; avoid repeated polling for static geocodes.
- Connector design: `GeoEnrichmentConnector` stores raw JSON responses and normalizes into `geo_entities`; link `geo_entities` to `company_entities`, evidence URLs, and topic packs.
- Compliance: Google Maps Platform terms, billing, display/attribution, and caching restrictions must be tracked per source. Do not store or reuse fields beyond allowed retention/use terms.
- Priority: P1 for company/geography enrichment and offline-market research.

## Paid Providers / MCP / OSS References

### Recommended Integration Candidates

| Provider | Coverage | Shape | MVP Fit | Adapter |
|---|---|---|---|---|
| Tavily | Web/news/search/extract/map/crawl | CLI/REST/MCP | P0 | `SearchProviderAdapter` |
| AnySearch | Web, vertical domains, batch, extract | CLI/JSON-RPC/MCP | P0 | `SearchProviderAdapter` with vertical routing |
| Apify | Actor marketplace, social/ecommerce/SERP/app stores | API/SDK/CLI/MCP | P0/P1 | `ApifyActorAdapter` |
| SociaVault | Social, ad libraries, YouTube, Reddit, X, TikTok, Instagram, LinkedIn | REST + OSS MCP | P0/P1 | `SociaVaultAdapter` |
| SocialCrawl | Broad social/commercial/search platform APIs | REST + MCP | P0/P1 | `SocialCrawlAdapter` with endpoint discovery |
| JustOneAPI | China/global social, ecommerce, WeChat, Zhihu, Bilibili, Douyin, Xiaohongshu | SDK/API/MCP claimed | P0/P1 | `JustOneAPIAdapter` |
| Bright Data | Enterprise social/ecommerce/web datasets | REST/datasets | P1 | `BrightDataAdapter` |
| ScrapeCreators | Social APIs and agent skills | REST/MCP/CLI claimed | P1 | `ScrapeCreatorsAdapter` |
| Trends-MCP | Trends across Google, YouTube, TikTok, Reddit, Amazon, GitHub, etc. | MCP | P1 | `TrendSignalAdapter` |

### OSS References To Study, Not Use As Production Defaults

| Project | Value | Use |
|---|---|---|
| Agent-Reach / social-reach | Cross-platform agent search patterns | Study CLI/MCP/channel taxonomy; optional local research utility |
| MediaCrawler | China platform schemas/session handling | Reference field mappings and Playwright patterns |
| OpenBiliClaw | Local-first multi-source adapter/recommendation architecture | Study `SourceAdapter`, dedupe/history, browser extension bridge |
| OpenCMO | Marketing/community monitoring workflows | Study report orchestration and source categories |
| Obsei | Observe/analyze/inform pipeline separation | Borrow architecture ideas |
| Reddit/YouTube/X MCP servers | Per-platform MCP tool shapes | Reference, but prefer first-party/provider adapters |

## Connector Interface

All connectors should implement:

```python
class SourceConnector:
    def test_connection(self) -> HealthCheck: ...
    def estimate_cost(self, task) -> CostEstimate: ...
    def plan_run(self, task, cursor, budget) -> RunPlan: ...
    def fetch_raw(self, plan) -> list[RawEnvelope]: ...
    def normalize(self, raw) -> list[EvidenceItem]: ...
    def next_cursor(self, run) -> dict: ...
```

Every `RawEnvelope` should include:

- `source_id`
- `task_id`
- `run_id`
- `platform_item_id`
- `url`
- `acquisition_layer`
- `session_profile_id` when applicable
- original response payload saved to `data/raw/...json`
- `raw_sha256`
- `content_hash`
- fetch timestamp

## Immediate Next Steps

1. Implement `SourceConnector` base classes and raw JSON store helper.
2. Implement SQLite schema for sources, topic packs, tasks, runs, raw items, evidence items, session profiles.
3. Build P0 connectors: Meta Search, GitHub, RSS/news, V2EX, Tianyan AI.
4. Add narrow pilots: Hacker News, Baidu Search ingestion, Bilibili sample connector.
5. Evaluate paid providers using identical test queries across SociaVault, SocialCrawl, JustOneAPI, Apify, Bright Data/ScrapeCreators.
