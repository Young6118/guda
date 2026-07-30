# MVP Roadmap

## Phase 0: Research and Design Bootstrap

Deliverables:

- Product brief
- Source strategy
- Architecture
- Data model
- MCP/API design
- GitHub and market reference list
- Compliance notes

Status: in progress.

## Phase 1: Source Registry and Task Management

Goal:

Create the core objects that let users and agents configure sources and collection tasks.

Build:

- Backend project skeleton.
- Database migrations for sources, topic packs, collection tasks, collection runs.
- CRUD API for sources and topic packs.
- CRUD API for collection tasks.
- Basic dashboard pages for sources/tasks/topic packs.
- MCP tools for `source_create`, `source_test`, `topic_pack_create`, `collection_task_create`.

Initial source types:

- Meta Search provider using web_search + Tavily + AnySearch + Baidu Search.
- GitHub API source.
- V2EX source.
- RSS/search source.
- Tianyan AI company enrichment source.
- AxData/eltdx/tdxquant-mcp A-share market data source for finance/company context.
- Google Maps MCP source for geocoding, places, routing, and distance context.
- Manual URL/CSV import source.

## Phase 2: First Collectors and Evidence Store

Goal:

Fetch real data from reliable sources and normalize it.

Build:

- GitHub issue/discussion collector.
- V2EX topic/reply collector.
- RSS/news collector.
- Meta Search collection adapter.
- Tianyan AI enrichment adapter.
- AxData/eltdx/tdxquant-mcp A-share market data adapter.
- Google Maps MCP geo-enrichment adapter.
- Raw item store.
- Evidence item normalization.
- Run logs and error handling.

Validation:

- AI Agents topic pack collects from GitHub + V2EX + RSS.
- Semiconductor topic pack collects from RSS/search + GitHub where relevant.
- Financial Markets topic pack collects from RSS/search/manual imports.

## Phase 3: Deduplication and Search

Goal:

Make collected evidence searchable and useful.

Build:

- Exact dedupe by source item id and URL.
- Text hash dedupe.
- SQLite FTS5 full-text search.
- Local embedding artifacts with SQLite pointers; defer vector DB until needed.
- Evidence search API and MCP tool.

## Phase 4: AI Signal Extraction

Goal:

Extract structured pain points and trend signals.

Build:

- Relevance classifier.
- Per-evidence signal extractor.
- Entity linker basics.
- Signal search and filter UI.
- Evaluation sample set.

## Phase 5: Clustering and Insight Cards

Goal:

Group repeated needs and generate cited insights.

Build:

- Embedding clustering job.
- Cluster label generator.
- Insight card generator.
- Review workflow.
- Cited weekly report for one topic pack.

## Phase 6: Paid Provider / External MCP Integrations

Goal:

Increase coverage without building brittle crawlers.

Evaluate and integrate 1-2 providers:

- Bright Data
- ScrapeCreators
- SociaVault
- SocialCrawl
- JustOneAPI
- Apify

Build:

- Provider adapter interface.
- Cost tracking per run.
- Sample quality comparison workflow.
- Admin approval for paid runs.

## Phase 7: Dashboard and Alerts

Goal:

Make insights operational.

Build:

- Topic pack dashboard.
- Trend velocity chart.
- Source coverage chart.
- Rising entities/phrases.
- Pain point map.
- Representative evidence table.
- Alerts for spikes and new high-confidence opportunities.

## Phase 8: Agent-Native Workflow Layer

Goal:

Let agents operate the system end-to-end.

Build:

- Full MCP server.
- Source discovery skill.
- Topic pack authoring skill.
- Evidence review skill.
- Opportunity synthesis skill.
- Scheduled briefs.

## Recommended First Implementation Stack

- Backend: FastAPI.
- Worker: in-process Python worker first; add RQ/Celery only if needed.
- Scheduler: APScheduler.
- Database: SQLite + FTS5.
- Raw store: local JSON files under `data/raw/`.
- Frontend: Next.js.
- MCP: FastMCP or TypeScript MCP SDK.
- AI: OpenAI-compatible abstraction.

## First Demo Scenario

Create three topic packs:

1. AI Agent Tools Watch.
2. Semiconductor Watch.
3. Financial Markets Watch.

Create sources:

- GitHub queries for agent tool repos and issues.
- V2EX relevant nodes/searches.
- RSS/search sources for semiconductor and financial news.
- Manual import for saved X/Reddit/Bilibili examples until provider integration is chosen.

Run:

- Hourly/daily collection tasks.
- Signal extraction.
- Weekly cited insight report.

Success criteria:

- At least 100 normalized evidence items collected.
- At least 20 extracted pain/trend signals.
- At least 5 reviewed insights with citations.
- At least 2 opportunity cards generated from evidence.
