from __future__ import annotations

import json
from pathlib import Path

from guda.collection import CollectionService
from guda.config import Settings
from guda.connectors.base import EvidenceDraft, RawEnvelope, SourceConnector
from guda.db import connect_db, init_db
from guda.repositories import Repository
from guda.raw_store import RawStore


class FakeConnector(SourceConnector):
    name = "fake"
    platform = "fake_search"
    acquisition_layer = "official_api"

    def __init__(self) -> None:
        self.fetch_count = 0

    def test_connection(self) -> bool:
        return True

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        self.fetch_count += 1
        return [
            RawEnvelope(
                platform_item_id="fake-1",
                url="https://example.com/item/1",
                title="A useful result",
                payload={"title": "A useful result", "url": "https://example.com/item/1", "text": query},
                fetched_at="2026-07-30T00:00:00Z",
            )
        ]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        return [
            EvidenceDraft(
                platform="fake_search",
                item_type="search_result",
                url=raw.url,
                title=raw.title,
                text=raw.payload["text"],
                author_display=None,
                created_at_source=None,
                engagement={},
            )
        ]


def test_collection_run_persists_raw_item_and_evidence(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    raw_store = RawStore(settings.raw_dir)
    service = CollectionService(repo=repo, raw_store=raw_store, connectors={"fake": FakeConnector()})

    source_id = repo.create_source(name="Fake Search", platform="fake", source_type="official_api")
    topic_id = repo.create_topic_pack(name="Semiconductor Watch", description="chips")
    task_id = repo.create_collection_task(
        name="fake task",
        topic_pack_id=topic_id,
        source_ids=[source_id],
        query="semiconductor pain points",
        max_items_per_run=5,
    )

    result = service.run_task(task_id)

    assert result.status == "completed"
    assert result.items_fetched == 1
    assert result.items_normalized == 1

    raw_rows = conn.execute("select raw_uri, content_hash from raw_items").fetchall()
    evidence_rows = conn.execute("select title, text, url from evidence_items").fetchall()
    assert len(raw_rows) == 1
    assert len(evidence_rows) == 1
    assert evidence_rows[0][0] == "A useful result"
    assert "semiconductor" in evidence_rows[0][1]

    raw_path = settings.data_dir / raw_rows[0][0]
    assert raw_path.exists()
    assert json.loads(raw_path.read_text())["title"] == "A useful result"

class RateLimitedConnector(FakeConnector):
    name = "limited"
    platform = "limited"

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        self.fetch_count += 1
        raise RuntimeError("429 Too Many Requests")


def _create_task(repo: Repository, *, platform: str) -> str:
    source_id = repo.create_source(name=platform, platform=platform, source_type="official_api")
    topic_id = repo.create_topic_pack(name="Rate Test", description="rate policy")
    return repo.create_collection_task(
        name="rate task",
        topic_pack_id=topic_id,
        source_ids=[source_id],
        query="agent",
        max_items_per_run=5,
    )


def test_collection_skips_source_when_rate_policy_is_cooling_down(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    raw_store = RawStore(settings.raw_dir)
    connector = FakeConnector()
    task_id = _create_task(repo, platform="fake")
    repo.upsert_rate_policy(platform="fake", min_interval_seconds=0, cooldown_seconds=60, burst_limit=1, enabled=True)
    repo.mark_platform_cooldown("fake", reason="manual test")
    service = CollectionService(repo=repo, raw_store=raw_store, connectors={"fake": connector})

    result = service.run_task(task_id)

    assert result.status == "completed"
    assert result.items_fetched == 0
    assert connector.fetch_count == 0


def test_collection_marks_cooldown_after_rate_limited_error(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    raw_store = RawStore(settings.raw_dir)
    connector = RateLimitedConnector()
    task_id = _create_task(repo, platform="limited")
    repo.upsert_rate_policy(platform="limited", min_interval_seconds=0, cooldown_seconds=60, burst_limit=1, enabled=True)
    service = CollectionService(repo=repo, raw_store=raw_store, connectors={"limited": connector})

    try:
        service.run_task(task_id)
    except RuntimeError:
        pass

    policy = repo.get_rate_policy("limited")
    assert connector.fetch_count == 1
    assert policy is not None
    assert policy["cooldown_until"] is not None
    assert "429" in policy["last_error"]
