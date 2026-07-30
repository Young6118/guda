from guda.source_catalog import source_catalog_as_dicts


def test_source_catalog_includes_planned_high_value_sources() -> None:
    catalog = {entry["platform"]: entry for entry in source_catalog_as_dicts()}

    for platform in [
        "reddit",
        "x_twitter",
        "youtube",
        "bilibili",
        "wechat_public",
        "xiaohongshu",
        "douyin",
        "app_reviews",
        "ecommerce_reviews",
        "google_maps",
        "ashare_market",
        "zhihu",
        "weibo",
        "xueqiu",
        "socialcrawl_provider",
        "tikhub_provider",
        "justoneapi_provider",
        "xpoz_provider",
        "sociavault_provider",
        "apify_provider",
        "mediacrawler_oss",
        "opencli_oss",
        "trends_mcp_provider",
    ]:
        assert platform in catalog
        assert catalog[platform]["connector_status"] in {"planned", "planned_gated", "gated", "implemented", "implemented_gated", "provider_gated", "oss_reference"}
