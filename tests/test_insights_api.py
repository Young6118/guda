from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings
from guda.connectors.base import EvidenceDraft
from guda.db import connect_db, init_db
from guda.raw_store import RawMetadata
from guda.repositories import Repository


def test_app_insights_returns_evidence_backed_cards(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    source_id = repo.create_source(name="GitHub", platform="github", source_type="official_api")
    topic_id = repo.create_topic_pack(name="AI Watch")
    task_id = repo.create_collection_task(name="watch", topic_pack_id=topic_id, source_ids=[source_id], query="agent")
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=1, items_normalized=1)
    raw_id = repo.insert_raw_item(source_id=source_id, task_id=task_id, run_id=run_id, platform_item_id="1", url="https://example.com/1", metadata=RawMetadata(raw_uri="raw/1.json", raw_sha256="sha", raw_size_bytes=1), acquisition_layer="official_api", fetched_at="2026-07-31T00:00:00Z", raw_content_hash="hash")
    repo.insert_evidence(raw_item_id=raw_id, source_id=source_id, fetched_at="2026-07-31T00:00:00Z", draft=EvidenceDraft(platform="github", item_type="issue", title="Agent deployment pain", text="Agent deployment needs better retry and observability", url="https://example.com/1", topics=["deployment"], entities=["Claude Code"]))
    conn.close()

    client = TestClient(create_app(settings))
    res = client.get("/api/app/insights", params={"topic_pack_id": topic_id, "days": 30}, auth=("admin", "secret"))

    assert res.status_code == 200
    body = res.json()
    assert body["summary"]["evidence_count"] == 1
    assert body["summary"]["period_days"] == 30
    assert any(card["type"] == "keyword" for card in body["insights"])
    assert any(card["type"] == "platform" for card in body["insights"])
