from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceCatalogEntry:
    platform: str
    priority: str
    connector_status: str
    suggested_path: str
    notes: str


SOURCE_CATALOG: list[SourceCatalogEntry] = [
    SourceCatalogEntry("meta_search", "P0", "implemented", "official_api/paid_provider", "Tavily-backed search adapter; Baidu/AnySearch can be layered in."),
    SourceCatalogEntry("github", "P0", "implemented", "official_api", "REST search for repos/issues/releases; add GraphQL discussions later."),
    SourceCatalogEntry("rss", "P0", "implemented", "public_endpoint", "RSS/Atom feed ingestion for blogs/news/changelogs."),
    SourceCatalogEntry("v2ex", "P0", "implemented", "official_api/public_endpoint", "API 2.0 with PAT; legacy latest-topic fallback without PAT."),
    SourceCatalogEntry("hackernews", "P0/P1", "implemented", "public_endpoint", "Algolia HN search for story evidence; Firebase comments later."),
    SourceCatalogEntry("huggingface", "P0", "implemented", "official_api", "Hugging Face Hub public model search; HF_TOKEN optional for private/higher-limit access."),
    SourceCatalogEntry("arxiv", "P0", "implemented", "public_endpoint", "arXiv Atom API for paper search; no key required; rate around one request per three seconds."),
    SourceCatalogEntry("baidu_search", "P0", "implemented_gated", "official_api", "Uses installed Baidu skill; requires valid BAIDU/Qianfan API key."),
    SourceCatalogEntry("tianyan_ai", "P0", "implemented", "official_api", "Uses tyc CLI for China company enrichment."),
    SourceCatalogEntry("reddit", "P0", "gated", "official_api/paid_provider", "Needs OAuth/commercial terms or provider adapter."),
    SourceCatalogEntry("x_twitter", "P0", "gated", "paid_provider/official_api", "High value but paid/limited; route via provider first."),
    SourceCatalogEntry("youtube", "P1", "planned", "official_api", "YouTube Data API key; comments/metadata first, transcripts where allowed."),
    SourceCatalogEntry("bilibili", "P1", "planned", "public_endpoint/paid_provider/logged_in_browser", "Narrow pilot for video metadata/comments/danmaku; provider for scale."),
    SourceCatalogEntry("wechat_public", "P1", "gated", "official_api/paid_provider/manual", "Owned account official stats; arbitrary account coverage via provider/manual."),
    SourceCatalogEntry("xiaohongshu", "P1", "gated", "paid_provider/logged_in_browser", "High value consumer demand; avoid broad unofficial scraping."),
    SourceCatalogEntry("douyin", "P1", "gated", "official_api/paid_provider", "Authorized accounts via official API; public search via provider."),
    SourceCatalogEntry("app_reviews", "P1", "planned", "official_api/paid_provider", "App Store Connect/Google Play owned reviews; provider for competitor coverage."),
    SourceCatalogEntry("ecommerce_reviews", "P1", "gated", "paid_provider", "Product sourcing and consumer complaint source; provider-first."),
    SourceCatalogEntry("google_maps", "P1", "planned", "official_api/MCP", "Requires Google Maps key; geocoding/POI/routing enrichment."),
    SourceCatalogEntry("ashare_market", "P1", "planned_gated", "public_endpoint/MCP/logged_in_browser", "AxData/eltdx/tdxquant-mcp; trading tools disabled; terms review needed."),
    SourceCatalogEntry("stackexchange", "P2/P1", "planned", "official_api", "Stable API for Q&A; useful after GitHub/HN."),
    SourceCatalogEntry("zhihu", "P2", "gated", "paid_provider/logged_in_browser", "High knowledge source; scraping risk."),
    SourceCatalogEntry("weibo", "P2", "gated", "paid_provider/manual", "Public sentiment/trends; API/login limitations."),
    SourceCatalogEntry("xueqiu", "P2", "gated", "paid_provider/logged_in_browser", "Finance sentiment; licensing/session risk."),
    SourceCatalogEntry("tavily_provider", "P0", "implemented", "official_api/MCP", "Web/news/search/extract provider already used by meta_search; TAVILY_API_KEY present on this machine."),
    SourceCatalogEntry("socialcrawl_provider", "P0/P1", "provider_gated", "paid_provider/MCP", "Unified API/MCP for 42-44 platforms, 264-357 endpoints; covers TikTok, Instagram, YouTube, X, Reddit, app stores, ecommerce, Trustpilot, Tripadvisor, Google News/Finance, HN, GitHub; needs SOCIALCRAWL_API_KEY."),
    SourceCatalogEntry("tikhub_provider", "P0/P1", "provider_gated", "paid_provider/MCP/SDK", "Unified REST/OpenAPI/Python SDK for 16+ platforms and 1000+ endpoints including Douyin, TikTok, Xiaohongshu, Bilibili, Weibo, Zhihu, YouTube, Reddit, WeChat; needs TIKHUB_API_KEY."),
    SourceCatalogEntry("justoneapi_provider", "P0/P1", "provider_gated", "paid_provider/SDK", "China/global API provider covering Xiaohongshu, Douyin, Bilibili, Weibo, WeChat, Zhihu, ecommerce and global platforms; needs provider key."),
    SourceCatalogEntry("xpoz_provider", "P1", "provider_gated", "paid_provider/MCP/SDK", "Indexed social intelligence for Twitter/X, Instagram, Reddit and TikTok; needs XPOZ_API_KEY."),
    SourceCatalogEntry("sociavault_provider", "P1", "provider_gated", "paid_provider/MCP", "MCP/API coverage for TikTok, Instagram, YouTube, X, LinkedIn, Facebook, Reddit, Threads, Pinterest, Twitch and ad libraries; needs SOCIAVAULT_API_KEY."),
    SourceCatalogEntry("apify_provider", "P1", "provider_gated", "paid_provider/MCP/actors", "Actor marketplace for social/ecommerce/SERP/app stores; schema varies by actor; needs APIFY_TOKEN."),
    SourceCatalogEntry("mediacrawler_oss", "P1", "oss_reference", "logged_in_browser/headless_authenticated", "Open-source China platform crawler covering XHS, Douyin, Kuaishou, Bilibili, Weibo, Tieba, Zhihu with login/proxy support; useful as schema/reference, not default production path."),
    SourceCatalogEntry("opencli_oss", "P1", "oss_reference", "logged_in_browser", "Browser-backed CLI adapters for XHS, Bilibili, Zhihu, Reddit, HN, Twitter/X and more; useful for manual/low-volume authenticated research."),
    SourceCatalogEntry("trends_mcp_provider", "P1", "provider_gated", "paid_provider/MCP", "Cross-platform trend indices for Google Search, YouTube, TikTok, Reddit, Amazon, Wikipedia, news, npm and more; needs provider key."),
]


def source_catalog_as_dicts() -> list[dict[str, str]]:
    return [asdict(entry) for entry in SOURCE_CATALOG]
