# GitHub and Market References

This project should learn from existing open-source projects, MCP servers, paid data APIs, and enterprise listening tools. The goal is not to copy one project wholesale, but to identify reusable patterns and integration candidates.

## Important Open-Source / GitHub References

### Agent-Reach

Reported as a high-star Python CLI/MCP-style tool that gives agents access to Twitter/X, Reddit, YouTube, GitHub, Bilibili, Xiaohongshu, and related sources.

Why it matters:

- Cross-platform agent-facing search/read abstraction.
- Strong inspiration for our MCP layer.
- Useful reference for source adapters and LLM-friendly output shaping.

Evaluate:

- Connector architecture.
- Supported platform coverage.
- Terms/compliance posture.
- Whether it can be integrated as a provider adapter.

### MediaCrawler

Multi-platform self-media crawler covering Xiaohongshu, Douyin, Kuaishou, Bilibili, Weibo, Tieba, Zhihu and comments.

Why it matters:

- Shows practical collector patterns for Chinese platforms.
- Useful for prototyping and understanding field schemas.
- Has explicit disclaimers; likely not suitable as-is for commercial production.

Evaluate:

- Data model fields.
- Browser context/login handling.
- Connector boundaries.
- Risk profile and rate controls.

### OpenBiliClaw

Local-first cross-platform AI content discovery agent covering Bilibili, Xiaohongshu, Douyin, YouTube, X, Zhihu, Reddit, Bangumi, and web.

Why it matters:

- Similar idea of breaking platform silos.
- Local profile + source adapter architecture is relevant.
- Cross-platform interest fusion is similar to our cross-source trend fusion.

Evaluate:

- SourceAdapter pattern.
- Deduplication and recommendation history.
- Local-first storage model.
- Browser extension architecture.

### OpenCMO

Open-source multi-agent AI marketing system with community monitoring across Reddit, HN, Dev.to, Bluesky, YouTube, X, V2EX, Weibo, Bilibili, Xueqiu, and stubs for Xiaohongshu/WeChat/Douyin.

Why it matters:

- Strong reference for marketing/growth topic packs.
- Has English and Chinese community source categories.
- Useful for agent orchestration and reporting patterns.

Evaluate:

- Community source implementations.
- Report format.
- Agent roles and workflows.

### Obsei

Low-code AI automation for social listening, alerting, brand image analysis, comparative studies, and unstructured data analysis.

Why it matters:

- Clear separation between observer/source and analyzer.
- Relevant source/analyzer abstraction.

Evaluate:

- Pipeline structure.
- Analyzer interfaces.
- Extensibility and current maintenance status.

### HasData Social Listening Tool

Small AI-powered social listening example using SERP API + LLM inference, charts, CSV reports, Telegram notifications.

Why it matters:

- Good minimal MVP shape.
- Useful for first dashboard/report structure.

### Reddit MCP Servers

Examples include reddit-mcp-buddy and mcp-server-reddit.

Why it matters:

- LLM-optimized Reddit browsing/search/comments API surface.
- Good examples for per-platform MCP tools.

### YouTube MCP Servers / Transcript Tools

Useful for video transcripts, comments, and content analysis.

Why it matters:

- Creator/video trend pack depends heavily on transcripts and comments.

### Trends-MCP

MCP server for trend data across Google Search, YouTube, TikTok, Reddit, Amazon, Wikipedia, news sentiment, web traffic, app downloads, Steam, npm, X/Twitter, GitHub, Spotify, Google Shopping, Google News, Google Images.

Why it matters:

- Very close to our trend-monitoring layer.
- Useful inspiration for tool taxonomy and source coverage.

### ScrapeCreators Social Media Research Skills

Agent skills for social listening briefs, product demand research, comment mining, competitor teardown, ad library analysis, and public social data workflows.

Why it matters:

- Strong model for our own skill layer.
- Shows workflow-level abstraction rather than raw endpoints.

### Bright Data Skills

Includes brand listening skills that collect across Reddit, X, Instagram, TikTok, YouTube, news, review sites, classify sentiment, cluster themes, and deliver cited digests.

Why it matters:

- Direct reference for paid data + agent skill integration.
- Useful for provider integration and benchmark output quality.

### SociaVault MCP / SocialCrawl MCP

MCP servers offering live access to profiles, posts, comments, search, trends, transcripts, ad libraries, ecommerce reviews, app reviews, and more.

Why it matters:

- Good candidates for paid/provider integration.
- Strong reference for MCP tool design and response shaping.

## Enterprise / Paid Product References

### Brandwatch

Enterprise consumer intelligence and social listening. Strong in data scale, dashboards, historical data, audience and brand monitoring.

Use as reference for:

- Query builder.
- Dashboard design.
- Historical trend analysis.
- Enterprise workflows.

### Talkwalker

Social listening with broad source coverage, visual/crisis monitoring.

Use as reference for:

- Visual listening.
- Alerting and crisis detection.
- Multi-source dashboards.

### Meltwater

PR/media monitoring + social listening.

Use as reference for:

- News + social integration.
- Earned media tracking.

### Sprinklr

Enterprise CX and social listening suite.

Use as reference for:

- Workflow orchestration.
- Role-based dashboards.
- Team review and action workflows.

### Pulsar

Audience intelligence and narrative/trend analysis.

Use as reference for:

- Audience segmentation.
- Narrative intelligence.
- Cultural/behavioral insights.

## Key Lessons

1. Do not start by building every scraper.
2. Build a source/provider abstraction that can integrate paid APIs, open-source tools, and internal connectors.
3. Design MCP tools around research workflows, not raw HTTP endpoints.
4. Make evidence citations a hard requirement.
5. Treat each source as having cost, coverage, compliance, quality, and freshness metadata.
6. Support both recurring monitoring and one-off deep research campaigns.
7. For semi-closed platforms, use paid/authorized access or human-in-the-loop workflows before attempting brittle crawling.
