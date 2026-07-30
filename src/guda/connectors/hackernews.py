from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class HackerNewsConnector:
    name = "hackernews"
    platform = "hackernews"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://hn.algolia.com", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/api/v1/search", params={"query": "test", "hitsPerPage": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/api/v1/search", params={"query": query, "hitsPerPage": limit, "tags": "story"})
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        raw = []
        for hit in response.json().get("hits", [])[:limit]:
            object_id = str(hit.get("objectID"))
            raw.append(RawEnvelope(platform_item_id=object_id, url=f"https://news.ycombinator.com/item?id={object_id}", title=hit.get("title") or hit.get("story_title"), payload={"provider": "algolia_hn", "hit": hit}, fetched_at=fetched_at))
        return raw

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        hit: dict[str, Any] = raw.payload.get("hit", {})
        text = hit.get("story_text") or hit.get("comment_text") or hit.get("title") or ""
        return [EvidenceDraft(platform="hackernews", item_type="story", url=raw.url, title=raw.title, text=text, author_display=hit.get("author"), created_at_source=hit.get("created_at"), engagement={"points": hit.get("points"), "comments": hit.get("num_comments"), "external_url": hit.get("url")})]
