from __future__ import annotations

import httpx

from guda.connectors.huggingface import HuggingFaceConnector


def test_huggingface_connector_normalizes_model_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "openai/gpt-oss", "modelId": "openai/gpt-oss", "likes": 10, "downloads": 100, "pipeline_tag": "text-generation", "tags": ["llm"], "lastModified": "2026-07-30T00:00:00.000Z"}])

    connector = HuggingFaceConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://huggingface.co"))

    raw = connector.fetch_raw("gpt", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert evidence.platform == "huggingface"
    assert evidence.item_type == "model"
    assert evidence.title == "openai/gpt-oss"
    assert evidence.engagement["downloads"] == 100
