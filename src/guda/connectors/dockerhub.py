from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class DockerHubConnector:
    name = "dockerhub"
    platform = "dockerhub"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://hub.docker.com", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/v2/search/repositories/", params={"query": "test", "page_size": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/v2/search/repositories/", params={"query": query, "page_size": limit})
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [self._envelope(item, fetched_at) for item in response.json().get("results", [])[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        item: dict[str, Any] = raw.payload.get("item", {})
        return [EvidenceDraft(platform="dockerhub", item_type="repository", url=raw.url, title=raw.title, text=item.get("short_description") or raw.title or "", author_display=item.get("repo_owner"), engagement={"stars": item.get("star_count"), "pulls": item.get("pull_count")})]

    @staticmethod
    def _envelope(item: dict[str, Any], fetched_at: str) -> RawEnvelope:
        name = item.get("repo_name") or item.get("name")
        return RawEnvelope(platform_item_id=name, url=f"https://hub.docker.com/r/{name}" if name else None, title=name, payload={"item": item}, fetched_at=fetched_at)
