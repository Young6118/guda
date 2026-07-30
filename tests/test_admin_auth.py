from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings


def test_admin_and_api_require_basic_auth_when_password_configured(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "app.sqlite",
        admin_username="admin",
        admin_password="secret",
    )
    client = TestClient(create_app(settings))

    assert client.get("/admin/").status_code == 401
    assert client.get("/app/").status_code == 401
    assert client.get("/api/rate-policies").status_code == 401

    ok = client.get("/api/rate-policies", auth=("admin", "secret"))
    assert ok.status_code == 200
    assert ok.json()[0]["platform"] == "arxiv"


def test_health_stays_public_when_admin_auth_enabled(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "app.sqlite",
        admin_username="admin",
        admin_password="secret",
    )
    client = TestClient(create_app(settings))

    assert client.get("/health").status_code == 200
