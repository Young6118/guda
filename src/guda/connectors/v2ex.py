from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class V2EXConnector:
    name = "v2ex"
    platform = "v2ex"
    acquisition_layer = "official_api"

    def __init__(self, *, client: httpx.Client | None = None, token: str | None = None, timeout_seconds: int = 30):
        headers = {"User-Agent": "guda/0.1"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.token = token
        self.client = client or httpx.Client(base_url="https://www.v2ex.com", headers=headers, timeout=timeout_seconds)

    def test_connection(self) -> bool:
        response = self.client.get("/api/v2/site/info")
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        node = self._node_from_query(query)
        if node and self.token:
            topics = self._get_result(f"/api/v2/nodes/{node}/topics")[:limit]
        else:
            topics = self._get_result("/api/topics/latest.json")[:limit]
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        raw: list[RawEnvelope] = []
        for topic in topics:
            topic_id = str(topic.get("id"))
            raw.append(
                RawEnvelope(
                    platform_item_id=f"topic:{topic_id}",
                    url=topic.get("url") or f"https://www.v2ex.com/t/{topic_id}",
                    title=topic.get("title"),
                    payload={"kind": "topic", "topic": topic},
                    fetched_at=fetched_at,
                )
            )
            replies_path = f"/api/v2/topics/{topic_id}/replies" if self.token else f"/api/replies/show.json?topic_id={topic_id}"
            replies = self._get_result(replies_path)[: max(0, limit - len(raw))]
            for reply in replies:
                reply_id = str(reply.get("id"))
                raw.append(
                    RawEnvelope(
                        platform_item_id=f"reply:{reply_id}",
                        url=f"https://www.v2ex.com/t/{topic_id}#reply{reply_id}",
                        title=topic.get("title"),
                        payload={"kind": "reply", "topic": topic, "reply": reply},
                        fetched_at=fetched_at,
                    )
                )
                if len(raw) >= limit:
                    return raw
        return raw[:limit]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        if raw.payload.get("kind") == "topic":
            topic = raw.payload["topic"]
            return [
                EvidenceDraft(
                    platform="v2ex",
                    item_type="topic",
                    url=raw.url,
                    title=topic.get("title"),
                    text=self._clean(topic.get("content") or topic.get("title") or ""),
                    author_display=(topic.get("member") or {}).get("username"),
                    created_at_source=self._timestamp(topic.get("created")),
                    engagement={"replies": topic.get("replies"), "node": (topic.get("node") or {}).get("name")},
                )
            ]
        reply = raw.payload["reply"]
        topic = raw.payload["topic"]
        return [
            EvidenceDraft(
                platform="v2ex",
                item_type="reply",
                url=raw.url,
                parent_url=topic.get("url") or f"https://www.v2ex.com/t/{topic.get('id')}",
                title=topic.get("title"),
                text=self._clean(reply.get("content") or ""),
                author_display=(reply.get("member") or {}).get("username"),
                created_at_source=self._timestamp(reply.get("created")),
                engagement={"topic_id": topic.get("id")},
            )
        ]

    def _get_result(self, path: str) -> list[dict[str, Any]]:
        response = self.client.get(path)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        result = data.get("result", data)
        if isinstance(result, list):
            return result
        return []

    @staticmethod
    def _node_from_query(query: str) -> str | None:
        for token in query.split():
            if token.startswith("node:") and len(token) > 5:
                return token.split(":", 1)[1]
        return None

    @staticmethod
    def _timestamp(value: Any) -> str | None:
        if value is None:
            return None
        try:
            return datetime.fromtimestamp(int(value), timezone.utc).isoformat().replace("+00:00", "Z")
        except (TypeError, ValueError, OSError):
            return None

    @staticmethod
    def _clean(value: str) -> str:
        return unescape(value).strip()
