from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Callable

from guda.connectors.base import EvidenceDraft, RawEnvelope


class BaiduSearchConnector:
    name = "baidu_search"
    platform = "baidu_search"
    acquisition_layer = "official_api"

    def __init__(self, *, runner: Callable[[str, int], dict[str, Any]] | None = None, timeout_seconds: int = 60):
        self.runner = runner
        self.timeout_seconds = timeout_seconds

    def test_connection(self) -> bool:
        return bool(self._run("测试", 1))

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        data = self._run(query, limit)
        items = data.get("results") or data.get("items") or data.get("data") or []
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        raw = []
        for index, item in enumerate(items[:limit], start=1):
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("link")
            title = item.get("title") or item.get("name")
            raw.append(RawEnvelope(platform_item_id=url or f"baidu:{index}", url=url, title=title, payload={"query": query, "result": item}, fetched_at=fetched_at))
        return raw

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        item = raw.payload.get("result", {})
        text = item.get("summary") or item.get("snippet") or item.get("description") or item.get("content") or raw.title or ""
        return [EvidenceDraft(platform="baidu_search", item_type="search_result", url=raw.url, title=raw.title, text=text, engagement={"source": item.get("source"), "rank": item.get("rank")})]

    def _run(self, query: str, limit: int) -> dict[str, Any]:
        if self.runner:
            return self.runner(query, limit)
        script = os.path.expanduser("~/.hermes/skills/baidu-search/scripts/search.py")
        env_file = os.path.expanduser("~/.hermes/.env")
        command = f"set -a; [ -f {env_file!r} ] && . {env_file!r}; set +a; python3 {script!r} {json.dumps(query)} --json --limit {int(limit)}"
        proc = subprocess.run(["bash", "-lc", command], capture_output=True, text=True, timeout=self.timeout_seconds, check=False)
        if proc.returncode != 0:
            return {}
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {}
