from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class GDELTConnector:
    name = "gdelt"
    platform = "gdelt"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://api.gdeltproject.org", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/api/v2/doc/doc", params={"query": "test", "mode": "artlist", "format": "json", "maxrecords": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/api/v2/doc/doc", params={"query": query, "mode": "artlist", "format": "json", "maxrecords": limit, "sort": "hybridrel"})
        if response.status_code == 429:
            raise RuntimeError("GDELT rate limited this request; retry later or reduce schedule frequency")
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [self._envelope(item, fetched_at) for item in response.json().get("articles", [])[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        item: dict[str, Any] = raw.payload.get("article", {})
        return [EvidenceDraft(platform="gdelt", item_type="article", url=raw.url, title=raw.title, text=item.get("title") or raw.title or "", created_at_source=item.get("seendate"), language=item.get("language"), engagement={"domain": item.get("domain"), "source_country": item.get("sourcecountry")})]

    @staticmethod
    def _envelope(item: dict[str, Any], fetched_at: str) -> RawEnvelope:
        return RawEnvelope(platform_item_id=item.get("url"), url=item.get("url"), title=item.get("title"), payload={"article": item}, fetched_at=fetched_at)
