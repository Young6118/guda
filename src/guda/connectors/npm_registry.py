from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class NPMRegistryConnector:
    name = "npm"
    platform = "npm"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://registry.npmjs.org", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/-/v1/search", params={"text": "test", "size": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/-/v1/search", params={"text": query, "size": limit})
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [self._envelope(obj, fetched_at) for obj in response.json().get("objects", [])[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        obj: dict[str, Any] = raw.payload.get("object", {})
        pkg = obj.get("package", {})
        links = pkg.get("links", {})
        return [EvidenceDraft(platform="npm", item_type="package", url=raw.url, title=raw.title, text=pkg.get("description") or raw.title or "", author_display=(pkg.get("publisher") or {}).get("username"), created_at_source=pkg.get("date"), engagement={"version": pkg.get("version"), "score": (obj.get("score") or {}).get("final"), "repository": links.get("repository")})]

    @staticmethod
    def _envelope(obj: dict[str, Any], fetched_at: str) -> RawEnvelope:
        pkg = obj.get("package", {})
        links = pkg.get("links", {})
        name = pkg.get("name")
        return RawEnvelope(platform_item_id=name, url=links.get("npm") or (f"https://www.npmjs.com/package/{name}" if name else None), title=name, payload={"object": obj}, fetched_at=fetched_at)
