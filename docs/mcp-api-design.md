# MCP and API Design

## Goal

Make the platform easy for AI agents and external systems to operate.

Agents should be able to:

- Discover candidate sources.
- Register sources.
- Create topic packs.
- Create collection tasks.
- Trigger one-off runs.
- Inspect evidence and run logs.
- Ask for trend and pain point analysis.
- Create aggregation/synthesis tasks.
- Promote findings into opportunity cards.

## API Surfaces

### REST API

Primary application API for dashboard and integrations.

Initial resources:

- `/sources`
- `/topic-packs`
- `/collection-tasks`
- `/collection-runs`
- `/evidence-items`
- `/clusters`
- `/insights`
- `/opportunities`
- `/reports`

### MCP Server

Agent-facing tool layer. MCP should wrap safe, high-level operations instead of exposing raw database writes.

## Initial MCP Tools

### `source_recommend`

Find likely data sources for a domain, topic, platform, or competitor.

Input:

```json
{
  "topic": "semiconductor supply chain",
  "region": "global",
  "languages": ["en", "zh"],
  "source_types": ["official_api", "rss", "paid_provider", "community"]
}
```

Output:

```json
{
  "candidates": [
    {
      "name": "Semiconductor industry news RSS pack",
      "platform": "rss",
      "source_type": "rss",
      "why": "Useful for hourly macro and industry updates",
      "access_notes": "low risk",
      "estimated_cost": "free"
    }
  ]
}
```

### `source_create`

Register a configured source.

Input:

```json
{
  "name": "V2EX AI Node",
  "platform": "v2ex",
  "source_type": "official_or_public_api",
  "query_template": "https://www.v2ex.com/api/topics/show.json?node_name=ai",
  "rate_limit_policy": "low volume, poll every 2h",
  "compliance_notes": "public community API; store public post metadata and replies"
}
```

### `source_test`

Validate source connectivity and return a small sample.

Input:

```json
{
  "source_id": "src_v2ex_ai",
  "sample_limit": 5
}
```

### `topic_pack_create`

Create a managed research theme.

Input:

```json
{
  "name": "Financial Markets Watch",
  "description": "Track retail and professional discussion around market direction, macro events, sectors, and trading pain points.",
  "keywords": ["stocks", "rates", "semiconductor", "liquidity", "earnings"],
  "entities": ["NVDA", "TSMC", "Fed", "NASDAQ"],
  "languages": ["en", "zh"],
  "regions": ["global", "US", "China"]
}
```

### `collection_task_create`

Create a recurring collection task.

Input:

```json
{
  "name": "Semiconductor Hourly News Scan",
  "topic_pack_id": "tp_semiconductor",
  "source_ids": ["src_google_news_semis", "src_rss_semis"],
  "query": "semiconductor supply chain AI chips lithography foundry packaging",
  "schedule": "every 1h",
  "lookback_window": "24h",
  "max_items_per_run": 200,
  "budget_per_run_usd": 1.5,
  "enabled": true
}
```

### `collection_task_run`

Trigger a task immediately.

Input:

```json
{
  "task_id": "task_semis_hourly",
  "reason": "manual verification"
}
```

### `aggregation_task_create`

Create an analysis job over collected evidence.

Input:

```json
{
  "name": "Weekly AI Agent Pain Point Map",
  "topic_pack_id": "tp_ai_agents",
  "time_range": "7d",
  "analysis_types": ["pain_points", "trend_shift", "feature_requests", "competitor_gaps"],
  "min_sources": 3,
  "require_citations": true
}
```

### `insight_search`

Search evidence-backed insights.

Input:

```json
{
  "query": "users complain agent tools are too expensive or unreliable",
  "topic_pack_id": "tp_ai_agents",
  "time_range": "30d",
  "limit": 20
}
```

### `evidence_search`

Search raw/normalized evidence.

Input:

```json
{
  "query": "Claude Code Codex WorkBuddy pain point pricing stuck context",
  "platforms": ["github", "reddit", "x", "v2ex"],
  "time_range": "14d",
  "limit": 50
}
```

### `company_enrich_tianyan`

Enrich a China company/entity using Tianyan AI via the configured `tyc` CLI/Skill. This tool should resolve ambiguous names first and avoid high-cost deep scans unless a task budget explicitly allows it.

Input:

```json
{
  "query": "宁德时代",
  "intent": "registration_info",
  "max_candidates": 5
}
```

Output:

```json
{
  "company_name": "宁德时代新能源科技股份有限公司",
  "credit_code": "91350900587527783P",
  "status": "存续",
  "source": "tianyan_ai",
  "citations": ["tyc company registration-info"]
}
```

### `opportunity_create_from_insights`

Promote a set of insights into an opportunity card.

Input:

```json
{
  "title": "Agent workflow observability for non-technical teams",
  "insight_ids": ["ins_001", "ins_002"],
  "hypothesis": "Users need a way to see why agents failed and replay successful workflows.",
  "target_audience": "AI tool users and operations teams"
}
```

## Agent Skills

The project should eventually ship skills that use the MCP/API.

### Source Discovery Skill

Helps an agent turn a vague research area into suggested sources and collection tasks.

Example prompt:

> Find reliable sources for semiconductor supply-chain pain points across English and Chinese communities, register them, and create a weekly monitoring plan.

### Topic Pack Authoring Skill

Creates topic pack definitions with keywords, entities, excluded terms, source recommendations, and schedule presets.

### Evidence Review Skill

Reviews insight cards for weak evidence, missing citations, overclaiming, and duplicate clusters.

### Opportunity Synthesis Skill

Turns evidence clusters into product opportunity briefs with persona, pain, existing alternatives, willingness-to-pay signals, and suggested validation experiments.

## Permissions and Safety

MCP tools should enforce safe defaults:

- Creating sources is allowed but activating high-cost paid sources requires approval.
- Browser-assisted collection tasks require explicit review.
- Bulk scraping settings require admin approval.
- Every paid/provider task needs a budget field.
- Every insight must expose citations and confidence.
