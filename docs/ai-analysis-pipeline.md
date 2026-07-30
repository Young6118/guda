# AI Analysis Pipeline

## Purpose

Use AI to turn large volumes of noisy public discussion into structured, cited, reviewable intelligence.

The pipeline should not replace evidence. It should compress evidence into inspectable findings.

## Pipeline Stages

### 1. Relevance Classification

Determine whether an evidence item belongs to a topic pack.

Inputs:

- Evidence text
- Source metadata
- Topic pack keywords/entities

Outputs:

- relevance score
- matched topic packs
- reason

### 2. Signal Extraction

Extract structured signals from individual evidence items.

Signal types:

- pain point
- feature request
- complaint
- workaround
- purchase intent
- churn / switching signal
- competitor mention
- trend signal
- solution idea
- unanswered question

Each signal should include:

- short summary
- exact quote
- severity
- urgency
- confidence
- entities

### 3. Entity Linking

Normalize references to products, companies, tools, industries, tickers, repos, and people.

Examples:

- `Claude Code`, `claude-code`, `cc` -> Claude Code
- `NVDA`, `Nvidia`, `英伟达` -> NVIDIA
- `小红书`, `rednote`, `XHS` -> Xiaohongshu

### 4. Deduplication

Remove repeated content while preserving source diversity.

Methods:

- exact URL/platform id dedupe
- text hash dedupe
- near-duplicate embedding similarity
- repost/quote relationship tracking

### 5. Clustering

Cluster extracted signals into themes.

MVP options:

- Embeddings + HDBSCAN / agglomerative clustering.
- BERTopic for topic representation.
- LLM label generation for human-readable names.

Cluster quality dimensions:

- coherence
- source diversity
- recency
- evidence count
- engagement weight
- cross-language match

### 6. Trend Scoring

Rank topics by movement, not only volume.

Features:

- mention velocity
- acceleration
- source diversity growth
- engagement-weighted change
- new entity co-occurrence
- novelty vs baseline

### 7. Insight Generation

Create a cited insight card from one or more clusters.

Insight card fields:

- title
- concise claim
- evidence summary
- representative quotes
- source/time distribution
- affected personas
- existing workaround
- opportunity angle
- confidence and caveats

### 8. Opportunity Synthesis

Combine multiple insights into a product/business opportunity.

Opportunity fields:

- target audience
- core pain
- triggering moments
- current alternatives
- why existing solutions fail
- willingness-to-pay signals
- possible AI-enabled solution paths
- validation experiments
- risks

### 9. Human Review Loop

AI outputs need review.

Review actions:

- approve insight
- reject weak insight
- request more evidence
- merge duplicate insights
- promote to opportunity
- create follow-up collection task

## Prompting Rules

All AI summaries must:

- cite evidence item ids or URLs
- distinguish fact from interpretation
- avoid claiming market size unless evidence supports it
- include uncertainty and source bias
- preserve user language for pain points
- avoid collapsing different personas into one claim

## Evaluation

Measure:

- precision of relevance classification
- extraction recall on labeled samples
- duplicate cluster quality
- citation correctness
- human approval rate
- insight usefulness rating
- cost per accepted insight

## Recommended MVP Models

- Cheap classifier/extractor model for per-item passes.
- Stronger reasoning model for cluster and opportunity synthesis.
- Local embeddings model or provider embeddings for semantic search.

## Agentic Enhancements

Agents can improve the pipeline by:

- discovering missing sources for weak clusters
- proposing new topic pack keywords/entities
- creating follow-up collection tasks
- comparing paid provider samples
- validating insights against original pages
- producing weekly intelligence briefs
