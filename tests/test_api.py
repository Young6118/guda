from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings
from guda.connectors.base import CompanyDraft, EvidenceDraft
from guda.db import connect_db
from guda.raw_store import RawMetadata
from guda.repositories import Repository, content_hash


def test_health_and_source_lifecycle(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    client = TestClient(create_app(settings))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    created = client.post(
        "/sources",
        json={"name": "Meta Search", "platform": "meta_search", "source_type": "official_api"},
    )
    assert created.status_code == 201
    source_id = created.json()["id"]

    listed = client.get("/sources")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == source_id


def test_evidence_and_company_search_apis(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    client = TestClient(create_app(settings))
    conn = connect_db(settings.database_path)
    repo = Repository(conn)
    source_id = repo.create_source(name="Fixture", platform="fixture", source_type="manual")
    topic_id = repo.create_topic_pack(name="AI Agent Tools")
    task_id = repo.create_collection_task(
        name="fixture task",
        topic_pack_id=topic_id,
        source_ids=[source_id],
        query="agent deployment pain",
    )
    run_id = repo.start_run(task_id)
    raw_item_id = repo.insert_raw_item(
        source_id=source_id,
        task_id=task_id,
        run_id=run_id,
        platform_item_id="fixture-1",
        url="https://example.com/agent",
        metadata=RawMetadata(raw_uri="raw/fixture.json", raw_sha256="0" * 64, raw_size_bytes=2),
        acquisition_layer="manual",
        fetched_at="2026-07-30T00:00:00Z",
        raw_content_hash=content_hash("fixture-1"),
    )
    repo.insert_evidence(
        raw_item_id=raw_item_id,
        source_id=source_id,
        fetched_at="2026-07-30T00:00:00Z",
        draft=EvidenceDraft(
            platform="fixture",
            item_type="post",
            url="https://example.com/agent",
            title="Agent deployment pain",
            text="Developers complain that agent deployment is too manual.",
        ),
    )
    repo.insert_company(
        source_id=source_id,
        draft=CompanyDraft(
            provider="tianyan_ai",
            company_name="宁德时代新能源科技股份有限公司",
            credit_code="91350900587527783P",
            registration_status="存续",
            industry="电气机械和器材制造业",
        ),
    )
    conn.close()

    evidence = client.get("/evidence/search", params={"query": "deployment", "limit": 5})
    assert evidence.status_code == 200
    assert evidence.json()[0]["title"] == "Agent deployment pain"
    assert evidence.json()[0]["platform"] == "fixture"

    companies = client.get("/companies/search", params={"query": "宁德时代"})
    assert companies.status_code == 200
    assert companies.json()[0]["credit_code"] == "91350900587527783P"


def test_source_test_endpoint_updates_health_status(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    client = TestClient(create_app(settings))
    created = client.post(
        "/sources",
        json={"name": "Unknown", "platform": "unknown_connector", "source_type": "manual"},
    )
    source_id = created.json()["id"]

    response = client.post(f"/sources/{source_id}/test")

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert response.json()["health_status"] == "error"
    assert "no connector" in response.json()["error"]
