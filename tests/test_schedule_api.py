from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings
from guda.db import connect_db, init_db
from guda.repositories import Repository


def test_task_schedule_can_be_enabled_and_validated(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    source_id = repo.create_source(name="RSS", platform="rss", source_type="rss")
    topic_id = repo.create_topic_pack(name="Watch")
    task_id = repo.create_collection_task(name="watch", topic_pack_id=topic_id, source_ids=[source_id], query="signal")
    conn.close()

    client = TestClient(create_app(settings))
    ok = client.patch(f"/api/app/tasks/{task_id}/schedule", json={"schedule": "2h", "enabled": True}, auth=("admin", "secret"))
    bad = client.patch(f"/api/app/tasks/{task_id}/schedule", json={"schedule": "weekly", "enabled": True}, auth=("admin", "secret"))
    detail = client.get(f"/api/app/tasks/{task_id}", auth=("admin", "secret"))

    assert ok.status_code == 200
    assert ok.json()["schedule"] == "2h"
    assert bad.status_code == 422
    assert detail.json()["task"]["schedule"] == "2h"
