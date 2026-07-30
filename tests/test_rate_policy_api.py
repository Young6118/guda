from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings


def test_rate_policy_api_lists_defaults_and_updates_policy(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")
    client = TestClient(create_app(settings))

    listed = client.get("/rate-policies")
    assert listed.status_code == 200
    platforms = {row["platform"]: row for row in listed.json()}
    assert platforms["arxiv"]["min_interval_seconds"] >= 3
    assert platforms["gdelt"]["cooldown_seconds"] >= 60

    updated = client.put(
        "/rate-policies/arxiv",
        json={
            "min_interval_seconds": 10,
            "cooldown_seconds": 120,
            "burst_limit": 1,
            "enabled": True,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["min_interval_seconds"] == 10
    assert updated.json()["cooldown_seconds"] == 120

    listed_again = client.get("/rate-policies")
    arxiv = {row["platform"]: row for row in listed_again.json()}["arxiv"]
    assert arxiv["min_interval_seconds"] == 10
