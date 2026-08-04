from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings
from guda.db import connect_db, init_db
from guda.repositories import Repository


def test_app_tasks_reports_task_run_health(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    source_id = repo.create_source(name="GitHub", platform="github", source_type="official_api")
    topic_id = repo.create_topic_pack(name="AI Watch")
    task_id = repo.create_collection_task(name="watch", topic_pack_id=topic_id, source_ids=[source_id], query="agent")
    run_id = repo.start_run(task_id)
    repo.finish_run(run_id, status="completed", items_fetched=3, items_normalized=2)
    conn.close()

    client = TestClient(create_app(settings))
    res = client.get("/api/app/tasks", params={"topic_pack_id": topic_id}, auth=("admin", "secret"))

    assert res.status_code == 200
    body = res.json()
    assert body["summary"]["task_count"] == 1
    assert body["tasks"][0]["monitor_status"] == "healthy"
    assert body["tasks"][0]["items_fetched"] == 3
