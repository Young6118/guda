# Data Model

## Design Goals

- Preserve raw evidence and citation links.
- Keep immutable original provider responses as local JSON files and store only pointers/hashes in SQLite.
- Support heterogeneous source schemas.
- Enable scheduled collection and one-off research campaigns.
- Support AI extraction, clustering, insight review, and opportunity synthesis.
- Track source reliability, cost, and compliance metadata.

## Core Tables

### `sources`

Represents one configured source.

Fields:

- `id`
- `name`
- `platform`
- `source_type`
- `access_status`
- `acquisition_ladder`
- `preferred_acquisition_layer`
- `max_allowed_acquisition_layer`
- `session_profile_id`
- `provider`
- `base_url`
- `query_template`
- `auth_profile_id`
- `rate_limit_policy`
- `cost_model`
- `coverage_notes`
- `compliance_notes`
- `health_status`
- `created_at`
- `updated_at`

### `topic_packs`

Managed monitoring/research themes.

Fields:

- `id`
- `name`
- `description`
- `keywords`
- `excluded_keywords`
- `entities`
- `languages`
- `regions`
- `priority`
- `owner`
- `created_at`
- `updated_at`

### `collection_tasks`

Scheduled or one-off data collection jobs.

Fields:

- `id`
- `name`
- `topic_pack_id`
- `source_ids`
- `query`
- `schedule`
- `lookback_window`
- `max_items_per_run`
- `budget_per_run_usd`
- `dedupe_policy`
- `enabled`
- `priority`
- `created_at`
- `updated_at`

### `collection_runs`

One execution of a collection task.

Fields:

- `id`
- `task_id`
- `started_at`
- `finished_at`
- `status`
- `items_fetched`
- `items_normalized`
- `items_deduped`
- `cost_usd`
- `error_summary`
- `run_log_uri`

### `raw_items`

Append-only index records pointing to local raw JSON files.

Raw file convention:

```text
data/raw/{source_id}/{YYYY}/{MM}/{DD}/{run_id}/{raw_item_id}.json
```

The JSON file contains the original provider response or extracted page payload plus fetch metadata. SQLite stores the pointer and integrity fields.

Fields:

- `id`
- `source_id`
- `task_id`
- `run_id`
- `platform_item_id`
- `url`
- `raw_uri`
- `raw_sha256`
- `raw_size_bytes`
- `acquisition_layer`: official_api, public_endpoint, paid_provider, logged_in_browser, headless_authenticated, manual
- `session_profile_id`
- `content_hash`
- `fetched_at`

### `session_profiles`

Browser or credential session references for controlled logged-in collection. The table stores metadata only; cookies/tokens should live in an encrypted/private runtime store, not in the main SQLite database when avoidable.

Fields:

- `id`
- `platform`
- `profile_name`
- `profile_type`: browser_context, cookie_store, oauth_token, manual
- `storage_ref`
- `owner`
- `status`: active, expired, revoked, needs_login
- `allowed_source_ids`
- `created_at`
- `updated_at`

### `company_entities`

Normalized company records enriched from authoritative sources such as Tianyan AI, filings, or A-share/F10 market-data sources.

Fields:

- `id`
- `source_id`
- `provider`: tianyan_ai, filings, axdata, eltdx, tdxquant_mcp, google_maps, manual, other
- `company_name`
- `credit_code`
- `company_id_provider`
- `stock_code`
- `exchange`
- `registration_status`
- `legal_person`
- `industry`
- `region`
- `registration_info_json`
- `risk_snapshot_json`
- `market_profile_json`
- `geo_profile_json`
- `last_enriched_at`
- `created_at`
- `updated_at`

### `market_observations`

Structured market data used as context for finance and company-topic analysis. These are not user evidence items; they should link to raw items and company entities but live in a separate layer.

Fields:

- `id`
- `raw_item_id`
- `source_id`
- `provider`: axdata, eltdx, tdxquant_mcp, exchange, paid_provider, manual
- `company_entity_id`
- `instrument_code`
- `exchange`
- `observation_type`: quote, kline, minute, trade_tick, auction, f10_profile, topic_membership, shortline_indicator, valuation, announcement, news, research_report
- `observed_at`
- `period`: tick, 1m, 5m, day, week, month, quarter, year, none
- `metrics_json`
- `topics_json`
- `url`
- `created_at`

### `geo_entities`

Geographic enrichment records from providers such as Google Maps. These link addresses, companies, venues, evidence, and topic packs to place/location context.

Fields:

- `id`
- `raw_item_id`
- `source_id`
- `provider`: google_maps, osm, paid_provider, manual
- `company_entity_id`
- `address_raw`
- `address_normalized`
- `place_id_provider`
- `place_name`
- `place_types`
- `latitude`
- `longitude`
- `viewport_json`
- `region`
- `country_code`
- `rating`
- `review_count`
- `opening_hours_json`
- `contact_json`
- `distance_matrix_json`
- `directions_json`
- `elevation_meters`
- `last_enriched_at`
- `created_at`
- `updated_at`

### `evidence_items`

Normalized atomic user expression.

Fields:

- `id`
- `raw_item_id`
- `source_id`
- `platform`
- `item_type`: post, comment, issue, discussion, article, review, transcript, danmaku, news, filing
- `author_display`
- `author_id_hash`
- `url`
- `parent_url`
- `title`
- `text`
- `language`
- `created_at_source`
- `fetched_at`
- `engagement`: JSON object for likes, replies, shares, stars, views, etc.
- `entities`
- `topics`
- `embedding_id`
- `text_hash`
- `near_duplicate_group_id`

### `extracted_signals`

AI/heuristic extracted structured observations from evidence.

Fields:

- `id`
- `evidence_item_id`
- `signal_type`: pain_point, feature_request, workaround, complaint, praise, purchase_intent, churn_risk, trend_signal, competitor_mention, solution_idea
- `summary`
- `quote`
- `severity`
- `urgency`
- `confidence`
- `model_name`
- `created_at`

### `clusters`

Groups similar signals/evidence.

Fields:

- `id`
- `topic_pack_id`
- `cluster_type`: semantic, trend, pain, entity, source_event
- `label`
- `description`
- `evidence_count`
- `source_diversity`
- `first_seen_at`
- `last_seen_at`
- `trend_score`
- `representative_evidence_ids`

### `insights`

Human/AI reviewed findings.

Fields:

- `id`
- `topic_pack_id`
- `cluster_ids`
- `title`
- `summary`
- `insight_type`: pain_point, trend, opportunity_signal, risk, competitor_gap, market_shift
- `confidence`
- `impact_score`
- `evidence_ids`
- `status`: draft, needs_more_evidence, reviewed, rejected, promoted
- `created_by`
- `created_at`
- `updated_at`

### `opportunities`

Product/business opportunities derived from insights.

Fields:

- `id`
- `title`
- `hypothesis`
- `target_audience`
- `pain_summary`
- `current_alternatives`
- `willingness_to_pay_signals`
- `solution_directions`
- `market_context`
- `risks`
- `validation_plan`
- `insight_ids`
- `evidence_ids`
- `confidence`
- `status`
- `created_at`
- `updated_at`

## Topic Pack Presets

### AI Agents

Entities:

- Codex
- Claude Code
- WorkBuddy
- Cursor
- OpenClaw
- Devin
- OpenCode
- MCP

Signals:

- Tool failure
- Reliability
- Price complaints
- Context limit
- Workflow automation requests
- Security and permissions concerns

### Semiconductor

Entities:

- NVIDIA
- TSMC
- ASML
- SMIC
- Samsung
- CUDA
- HBM
- lithography
- advanced packaging

Signals:

- Supply constraint
- Pricing pressure
- export control
- customer demand
- startup tooling gaps
- engineering bottlenecks

### Financial Markets

Entities:

- Fed
- Nasdaq
- S&P 500
- BTC
- gold
- oil
- major tickers

Signals:

- Sentiment shift
- retail panic/euphoria
- liquidity narrative
- earnings surprises
- macro concern
- sector rotation

### Creator Tools

Entities:

- YouTube
- TikTok
- Douyin
- Bilibili
- CapCut
- Runway
- Pika
- Sora-like tools

Signals:

- Editing bottlenecks
- script generation needs
- localization needs
- thumbnail/title optimization
- workflow fatigue
- monetization pain
