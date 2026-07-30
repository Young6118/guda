from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings
from guda.connectors.base import EvidenceDraft
from guda.db import connect_db, init_db
from guda.raw_store import RawMetadata
from guda.repositories import Repository


def seed_evidence(repo: Repository, source_id: str, task_id: str, run_id: str) -> None:
    raw_id = repo.insert_raw_item(
        source_id=source_id,
        task_id=task_id,
        run_id=run_id,
        platform_item_id="item-1",
        url="https://example.com/a",
        metadata=RawMetadata(raw_uri="raw/a.json", raw_sha256="abc", raw_size_bytes=3),
        acquisition_layer="official_api",
        fetched_at="2026-07-30T00:00:00Z",
        raw_content_hash="hash-a",
    )
    repo.insert_evidence(
        raw_item_id=raw_id,
        source_id=source_id,
        fetched_at="2026-07-30T00:00:00Z",
        draft=EvidenceDraft(
            platform="github",
            item_type="issue",
            title="Agent deployment failure",
            text="Users complain about deployment observability and retry failures",
            url="https://example.com/a",
            engagement={"score": 5},
            topics=["agent", "deployment"],
        ),
    )


def test_app_overview_and_evidence_are_backend_paginated(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    source_id = repo.create_source(name="GitHub", platform="github", source_type="official_api")
    topic_id = repo.create_topic_pack(name="AI Agent Watch", description="agents")
    task_id = repo.create_collection_task(name="task", topic_pack_id=topic_id, source_ids=[source_id], query="agent")
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=1, items_normalized=1)
    seed_evidence(repo, source_id, task_id, run_id)
    conn.close()

    client = TestClient(create_app(settings))
    overview = client.get("/api/app/overview", auth=("admin", "secret"))
    evidence = client.get("/api/app/evidence", params={"q": "deployment", "page": 1, "page_size": 5}, auth=("admin", "secret"))

    assert overview.status_code == 200
    assert overview.json()["metrics"]["evidence_items"] == 1
    assert overview.json()["platforms"][0]["platform"] == "github"
    assert evidence.status_code == 200
    assert evidence.json()["total"] == 1
    assert evidence.json()["items"][0]["title"] == "Agent deployment failure"
