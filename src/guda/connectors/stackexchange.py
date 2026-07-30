from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class StackExchangeConnector:
    name = "stackexchange"
    platform = "stackexchange"
    acquisition_layer = "official_api"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://api.stackexchange.com", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/2.3/info", params={"site": "stackoverflow"})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/2.3/search/advanced", params={"site": "stackoverflow", "q": query, "pagesize": limit, "order": "desc", "sort": "activity", "filter": "withbody"})
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [self._envelope(item, fetched_at) for item in response.json().get("items", [])[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        item: dict[str, Any] = raw.payload.get("item", {})
        return [EvidenceDraft(platform="stackexchange", item_type="question", url=raw.url, title=raw.title, text=item.get("body") or item.get("title") or "", author_display=(item.get("owner") or {}).get("display_name"), created_at_source=str(item.get("creation_date")) if item.get("creation_date") else None, engagement={"score": item.get("score"), "answers": item.get("answer_count"), "views": item.get("view_count")}, topics=item.get("tags") or [])]

    @staticmethod
    def _envelope(item: dict[str, Any], fetched_at: str) -> RawEnvelope:
        return RawEnvelope(platform_item_id=str(item.get("question_id")), url=item.get("link"), title=item.get("title"), payload={"item": item}, fetched_at=fetched_at)
