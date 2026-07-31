from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings
from guda.connectors.base import EvidenceDraft
from guda.db import connect_db, init_db
from guda.raw_store import RawMetadata
from guda.repositories import Repository

AUTH = ("admin", "secret")


def seed_base(tmp_path: Path) -> tuple[TestClient, Repository, str, str, str]:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    source_id = repo.create_source(name="GitHub", platform="github", source_type="official_api")
    topic_id = repo.create_topic_pack(name="AI Agent Watch", description="agents")
    task_id = repo.create_collection_task(name="task", topic_pack_id=topic_id, source_ids=[source_id], query="agent")
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    return TestClient(create_app(settings)), repo, source_id, topic_id, task_id


def seed_evidence(
    repo: Repository,
    source_id: str,
    task_id: str,
    run_id: str,
    *,
    suffix: str,
    platform: str = "github",
    item_type: str = "issue",
    language: str = "en",
    title: str | None = None,
    text_hash: str | None = None,
    entities: list[str] | None = None,
    raw_content_hash: str | None = None,
    url_suffix: str | None = None,
) -> str:
    content_hash = raw_content_hash or f"hash-{suffix}"
    url_suffix = url_suffix or suffix
    raw_id = repo.insert_raw_item(
        source_id=source_id,
        task_id=task_id,
        run_id=run_id,
        platform_item_id=f"item-{suffix}",
        url=f"https://example.com/{url_suffix}",
        metadata=RawMetadata(raw_uri=f"raw/{suffix}.json", raw_sha256=f"sha-{suffix}", raw_size_bytes=3),
        acquisition_layer="official_api",
        fetched_at=f"2026-07-30T00:0{suffix}:00Z",
        raw_content_hash=content_hash,
    )
    return repo.insert_evidence(
        raw_item_id=raw_id,
        source_id=source_id,
        fetched_at=f"2026-07-30T00:0{suffix}:00Z",
        draft=EvidenceDraft(
            platform=platform,
            item_type=item_type,
            title=title or f"Agent deployment failure {suffix}",
            text="Users complain about deployment observability and retry failures",
            url=f"https://example.com/{url_suffix}",
            language=language,
            engagement={"score": 5 + int(suffix)},
            entities=entities or ["Claude Code", "GUDA"],
            topics=["agent", "deployment"],
        ),
    )


def test_app_overview_and_evidence_are_backend_paginated(tmp_path: Path) -> None:
    client, repo, source_id, _, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    seed_evidence(repo, source_id, task_id, run_id, suffix="1")
    seed_evidence(repo, source_id, task_id, run_id, suffix="2", raw_content_hash="hash-2")
    repo.conn.close()

    overview = client.get("/api/app/overview", auth=AUTH)
    evidence = client.get("/api/app/evidence", params={"q": "deployment", "page": 1, "page_size": 1}, auth=AUTH)

    assert overview.status_code == 200
    assert overview.json()["metrics"]["evidence_items"] == 2
    assert overview.json()["platforms"][0]["platform"] == "github"
    assert evidence.status_code == 200
    assert evidence.json()["total"] == 2
    assert len(evidence.json()["items"]) == 1


def test_evidence_items_filters_sorts_and_paginates(tmp_path: Path) -> None:
    client, repo, source_id, _, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    seed_evidence(repo, source_id, task_id, run_id, suffix="1", language="en")
    seed_evidence(repo, source_id, task_id, run_id, suffix="2", language="zh")
    repo.conn.close()

    res = client.get(
        "/api/evidence-items",
        params={"q": "deployment", "platform": "github", "language": "zh", "sort": "fetched_at", "direction": "desc", "page": 1, "page_size": 5},
        auth=AUTH,
    )

    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["language"] == "zh"
    assert body["items"][0]["source"]["name"] == "GitHub"
    assert "deployment" in body["items"][0]["snippet"].lower()


def test_evidence_detail_returns_source_and_citation(tmp_path: Path) -> None:
    client, repo, source_id, _, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=1, items_normalized=1)
    evidence_id = seed_evidence(repo, source_id, task_id, run_id, suffix="1")
    repo.conn.close()

    res = client.get(f"/api/evidence-items/{evidence_id}", auth=AUTH)

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == evidence_id
    assert body["source"]["platform"] == "github"
    assert body["citations"]["url"] == "https://example.com/1"
    assert body["citations"]["raw_item_id"].startswith("raw_")


def test_evidence_facets_returns_platforms_types_languages_sources(tmp_path: Path) -> None:
    client, repo, source_id, _, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    seed_evidence(repo, source_id, task_id, run_id, suffix="1", language="en")
    seed_evidence(repo, source_id, task_id, run_id, suffix="2", item_type="discussion", language="zh")
    repo.conn.close()

    res = client.get("/api/evidence/facets", auth=AUTH)

    assert res.status_code == 200
    body = res.json()
    assert body["platforms"][0]["value"] == "github"
    assert {item["value"] for item in body["item_types"]} == {"discussion", "issue"}
    assert {item["value"] for item in body["languages"]} == {"en", "zh"}
    assert body["sources"][0]["name"] == "GitHub"


def test_topic_dashboard_counts_evidence_for_topic_pack_tasks(tmp_path: Path) -> None:
    client, repo, source_id, topic_id, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    seed_evidence(repo, source_id, task_id, run_id, suffix="1", entities=["Claude Code", "OpenAI"])
    seed_evidence(repo, source_id, task_id, run_id, suffix="2", entities=["Claude Code"])
    repo.conn.close()

    res = client.get(f"/api/topic-packs/{topic_id}/dashboard", auth=AUTH)

    assert res.status_code == 200
    body = res.json()
    assert body["summary"]["evidence_count"] == 2
    assert body["summary"]["source_count"] == 1
    assert body["rising_entities"][0]["entity"] == "Claude Code"


def test_topic_trends_returns_volume_platforms_and_entities(tmp_path: Path) -> None:
    client, repo, source_id, topic_id, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    seed_evidence(repo, source_id, task_id, run_id, suffix="1", entities=["Claude Code"])
    seed_evidence(repo, source_id, task_id, run_id, suffix="2", entities=["OpenAI"])
    repo.conn.close()

    res = client.get(f"/api/topic-packs/{topic_id}/trends", params={"bucket": "day", "limit": 5}, auth=AUTH)

    assert res.status_code == 200
    body = res.json()
    assert body["range"]["bucket"] == "day"
    assert body["volume"][0]["evidence_count"] == 2
    assert body["platforms"][0] == {"platform": "github", "evidence_count": 2}
    assert {item["entity"] for item in body["rising_entities"]} == {"OpenAI"}


def test_topic_dashboard_representative_evidence_dedupes_text_hash(tmp_path: Path) -> None:
    client, repo, source_id, topic_id, task_id = seed_base(tmp_path)
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=2, items_normalized=2)
    shared_hash = "shared-hash"
    seed_evidence(repo, source_id, task_id, run_id, suffix="1", text_hash=shared_hash, title="A")
    seed_evidence(repo, source_id, task_id, run_id, suffix="2", text_hash=shared_hash, title="A", raw_content_hash="shared-hash-2", url_suffix="1")
    repo.conn.close()

    res = client.get(f"/api/topic-packs/{topic_id}/dashboard", auth=AUTH)

    assert res.status_code == 200
    assert len(res.json()["representative_evidence"]) == 1
