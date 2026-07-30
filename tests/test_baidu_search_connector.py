from __future__ import annotations

import json

from guda.connectors.baidu_search import BaiduSearchConnector


def test_baidu_search_connector_normalizes_cli_results() -> None:
    def runner(query: str, limit: int) -> dict:
        return {"results": [{"title": "半导体供应链", "url": "https://example.cn/a", "summary": "国产替代需求增加", "source": "example"}]}

    connector = BaiduSearchConnector(runner=runner)

    raw_items = connector.fetch_raw("半导体 供应链", 5)
    evidence = connector.normalize(raw_items[0])

    assert raw_items[0].title == "半导体供应链"
    assert evidence[0].platform == "baidu_search"
    assert "国产替代" in evidence[0].text
