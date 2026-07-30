# Architecture

## System Shape

Global User Data Analysis should be an agent-native intelligence platform.

It has four interfaces:

1. Web dashboard for humans.
2. REST/GraphQL API for applications and internal services.
3. MCP server for AI agents to manage sources, tasks, evidence, and insights.
4. Skills/workflows that help agents discover new sources, evaluate data quality, and create collection tasks.

## High-Level Components

```text
Source Registry
  -> Collection Scheduler
  -> Source Connectors / Provider Adapters
  -> Raw Evidence Store
  -> Normalization Pipeline
  -> Deduplication + Entity Linking
  -> Embeddings + Search Indexes
  -> Topic/Trend/Pain Analysis
  -> Insight Review + Citation Store
  -> Dashboard / API / MCP
```

## Core Services

### Source Registry Service

Manages information sources, credentials, provider metadata, compliance notes, and connector configuration.

Responsibilities:

- Create/update/delete sources.
- Validate source configuration.
- Track source health and cost.
- Attach sources to topic packs and collection tasks.

### Collection Scheduler

Runs recurring collection tasks by source and topic pack.

Responsibilities:

- Cron/interval scheduling.
- Per-source rate limiting.
- Per-task budget limits.
- Backfill and lookback windows.
- Retry and dead-letter queue.
- Run logs and observability.

Suggested early implementation:

- Python + APScheduler or Celery Beat for MVP.
- Move to Temporal/Dagster/Airflow when pipelines get complex.

### Connector Runtime

Runs source-specific collectors.

Connector classes:

- Official API connectors.
- Paid provider connectors.
- Browser-assisted connectors.
- RSS/search connectors.
- Manual import connectors.

Each connector should emit a common raw event envelope.

### Raw Evidence Store

Append-only storage for fetched content before transformation.

Store:

- Original response payload.
- Fetch metadata.
- Source/task/run ids.
- URL/permalink.
- Content hash.
- Capture timestamp.

Suggested early implementation:

- Local JSON files for original raw payloads under `data/raw/`.
- SQLite stores raw file pointers, hashes, metadata, normalized records, and run state.
- Object storage can replace `data/raw/` later without changing the logical raw item model.

### Normalization Pipeline

Converts platform-specific data into normalized evidence items.

Examples:

- GitHub issue -> evidence item.
- Reddit post/comment -> evidence item.
- Bilibili comment/danmaku -> evidence item.
- WeChat article/comment -> evidence item.
- X post/reply -> evidence item.

### Deduplication and Entity Linking

Deduplicates exact and near-duplicate content.

Signals:

- URL/permalink.
- Platform item id.
- Text hash.
- SimHash/MinHash.
- Embedding similarity.
- Quoted/reposted relationship.

Entity linking:

- Products.
- Companies.
- People/accounts.
- Repositories.
- Technologies.
- Tickers/assets.
- Industries.

### Search and Analytics Index

Two complementary search paths:

- Keyword/filter search: SQLite FTS5 for MVP.
- Semantic search: local embedding files with SQLite pointers first; sqlite-vec/sqlite-vss, Qdrant, or another vector store later if needed.

MVP recommendation:

- SQLite-first: one local database for source registry, task state, normalized evidence, FTS5 indexes, signals, clusters, and insights.
- Local JSON raw store: keep immutable original responses outside SQLite to keep the DB small and easy to back up.

### AI Analysis Pipeline

Multi-stage AI-assisted analysis:

1. Classify content relevance to topic packs.
2. Extract claims, pains, tasks, requests, blockers, workarounds, willingness-to-pay signals.
3. Cluster similar evidence.
4. Generate topic labels and pain summaries.
5. Rank by recurrence, urgency, engagement, recency, and cross-source diversity.
6. Produce insight cards with citations.
7. Produce opportunity cards with confidence and next research steps.

### Review Layer

Not every AI output should be trusted as final.

Add review states:

- draft
- needs_more_evidence
- reviewed
- rejected
- promoted_to_opportunity

## Data Flow

1. User or agent creates a topic pack.
2. User or agent creates sources or imports source recommendations.
3. User or agent creates collection tasks with schedule, keywords, source set, and budget.
4. Scheduler runs the task.
5. Connectors fetch raw data.
6. Normalizer emits evidence items.
7. Dedupe/entity linker enriches items.
8. AI pipeline extracts structured signals and clusters them.
9. Dashboard/API/MCP expose insights.
10. Agents can create follow-up collection tasks to fill evidence gaps.

## Deployment Direction

MVP:

- Backend: FastAPI or NestJS.
- Database: SQLite + FTS5.
- Raw store: local JSON files under `data/raw/`.
- Queue: in-process worker / SQLite-backed job table first; Redis/RQ only when concurrency requires it.
- Scheduler: APScheduler.
- Frontend: Next.js or React dashboard.
- Connectors: Python workers.
- AI: provider-agnostic OpenAI-compatible client.
- MCP: FastMCP or TypeScript MCP SDK.

Production:

- Temporal/Dagster for orchestration.
- Object storage for raw JSON/media and exports.
- PostgreSQL + pgvector or ClickHouse/OpenSearch only when data volume or multi-user concurrency demands it.
- OpenSearch for large-scale faceted search.
- ClickHouse for time-series analytics.
- Role-based access and audit logs.

## Key Non-Functional Requirements

- Every insight must cite evidence.
- Every source must have access and compliance metadata.
- Every collection run must be auditable.
- Paid provider costs must be budgeted per source/task.
- The system must support both recurring monitoring and one-off research campaigns.
- The system must avoid aggressive scraping patterns and respect source constraints.
