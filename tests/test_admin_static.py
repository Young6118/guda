from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings


def test_user_app_serves_vue_build_when_present(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    client = TestClient(create_app(settings))
    page = client.get("/app/", auth=("admin", "secret"))
    assert page.status_code == 200
    assert "GUDA Intelligence" in page.text


def test_admin_javascript_builds_api_base_from_admin_prefix(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    client = TestClient(create_app(settings))

    js = client.get("/admin/assets/admin.js", auth=("admin", "secret"))

    assert js.status_code == 200
    assert "adminIndex" in js.text
    assert "apiBase" in js.text
