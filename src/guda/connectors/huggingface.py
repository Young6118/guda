from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class HuggingFaceConnector:
    name = "huggingface"
    platform = "huggingface"
    acquisition_layer = "official_api"

    def __init__(self, *, client: httpx.Client | None = None, token: str | None = None, timeout_seconds: int = 30):
        headers = {"User-Agent": "guda/0.1"}
        auth_token = token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        self.client = client or httpx.Client(base_url="https://huggingface.co", timeout=timeout_seconds, headers=headers)

    def test_connection(self) -> bool:
        response = self.client.get("/api/models", params={"search": "bert", "limit": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/api/models", params={"search": query, "limit": limit, "sort": "downloads", "direction": -1, "full": "true"})
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data = response.json()
        return [self._envelope(item, fetched_at) for item in (data if isinstance(data, list) else [])[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        item: dict[str, Any] = raw.payload.get("model", {})
        model_id = item.get("modelId") or item.get("id") or raw.title
        text = item.get("cardData", {}).get("summary") if isinstance(item.get("cardData"), dict) else None
        return [EvidenceDraft(platform="huggingface", item_type="model", url=raw.url, title=model_id, text=text or model_id or "", created_at_source=item.get("createdAt") or item.get("lastModified"), engagement={"downloads": item.get("downloads"), "likes": item.get("likes"), "pipeline_tag": item.get("pipeline_tag"), "library_name": item.get("library_name")}, topics=item.get("tags") or [])]

    @staticmethod
    def _envelope(item: dict[str, Any], fetched_at: str) -> RawEnvelope:
        model_id = item.get("modelId") or item.get("id")
        return RawEnvelope(platform_item_id=model_id, url=f"https://huggingface.co/{model_id}" if model_id else None, title=model_id, payload={"model": item}, fetched_at=fetched_at)
