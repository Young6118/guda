from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RawMetadata:
    raw_uri: str
    raw_sha256: str
    raw_size_bytes: int


class RawStore:
    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir

    def write(
        self,
        *,
        source_id: str,
        run_id: str,
        raw_item_id: str,
        payload: dict[str, Any],
        fetched_at: str | None = None,
    ) -> RawMetadata:
        dt = self._parse_datetime(fetched_at)
        rel_path = Path("raw") / source_id / f"{dt.year:04d}" / f"{dt.month:02d}" / f"{dt.day:02d}" / run_id / f"{raw_item_id}.json"
        abs_path = self.raw_dir.parent / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        abs_path.write_bytes(data)
        return RawMetadata(raw_uri=rel_path.as_posix(), raw_sha256=hashlib.sha256(data).hexdigest(), raw_size_bytes=len(data))

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
