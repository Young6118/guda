from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class DevToConnector:
    name = "devto"
    platform = "devto"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://dev.to", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/api/articles", params={"per_page": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/api/articles", params={"tag": query.split()[0], "per_page": limit, "top": 30})
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data = response.json()
        return [self._envelope(item, fetched_at) for item in (data if isinstance(data, list) else [])[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        item: dict[str, Any] = raw.payload.get("item", {})
        return [EvidenceDraft(platform="devto", item_type="article", url=raw.url, title=raw.title, text=item.get("description") or item.get("body_markdown") or raw.title or "", author_display=(item.get("user") or {}).get("username"), created_at_source=item.get("published_at"), engagement={"reactions": item.get("public_reactions_count"), "comments": item.get("comments_count")}, topics=item.get("tag_list") or [])]

    @staticmethod
    def _envelope(item: dict[str, Any], fetched_at: str) -> RawEnvelope:
        return RawEnvelope(platform_item_id=str(item.get("id")), url=item.get("url"), title=item.get("title"), payload={"item": item}, fetched_at=fetched_at)
