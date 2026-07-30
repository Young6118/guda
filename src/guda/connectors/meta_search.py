from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any

from guda.connectors.base import EvidenceDraft, RawEnvelope


class MetaSearchConnector:
    name = "meta_search"
    platform = "meta_search"
    acquisition_layer = "official_api"

    def __init__(self, *, timeout_seconds: int = 60):
        self.timeout_seconds = timeout_seconds

    def test_connection(self) -> bool:
        return bool(self._run_tavily("Hermes Agent", 1))

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        results = self._run_tavily(query, limit)
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        envelopes: list[RawEnvelope] = []
        for index, item in enumerate(results[:limit], start=1):
            url = item.get("url")
            title = item.get("title")
            envelopes.append(
                RawEnvelope(
                    platform_item_id=url or f"tavily-{index}",
                    url=url,
                    title=title,
                    payload={"provider": "tavily", "query": query, "result": item},
                    fetched_at=fetched_at,
                )
            )
        return envelopes

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        result = raw.payload.get("result", {})
        text = result.get("content") or result.get("raw_content") or raw.title or raw.url or ""
        return [
            EvidenceDraft(
                platform="tavily",
                item_type="search_result",
                url=raw.url,
                title=raw.title,
                text=text,
                engagement={"score": result.get("score")},
            )
        ]

    def _run_tavily(self, query: str, limit: int) -> list[dict[str, Any]]:
        env = os.environ.copy()
        hermes_env = os.path.expanduser("~/.hermes/.env")
        command = (
            f"set -a; [ -f {hermes_env!r} ] && . {hermes_env!r}; set +a; "
            f"tvly search {json.dumps(query)} --max-results {int(limit)} --json"
        )
        completed = subprocess.run(
            ["bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            return []
        data = json.loads(completed.stdout)
        return list(data.get("results", []))
