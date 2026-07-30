from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from guda.api import create_app
from guda.config import Settings


def test_admin_sources_endpoint_filters_sorts_and_paginates_in_backend(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    client = TestClient(create_app(settings))
    for name, platform in [("Alpha", "github"), ("Beta", "arxiv"), ("Gamma", "github")]:
        assert client.post("/sources", json={"name": name, "platform": platform, "source_type": "official_api"}).status_code == 201

    res = client.get("/api/admin/sources", params={"q": "github", "sort": "name", "direction": "desc", "page": 1, "page_size": 1}, auth=("admin", "secret"))

    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Gamma"


def test_admin_companies_endpoint_dedupes_by_company_identity(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite", admin_username="admin", admin_password="secret")
    client = TestClient(create_app(settings))
    source_id = client.post("/sources", json={"name": "Tianyan", "platform": "tianyan_ai", "source_type": "official_api"}).json()["id"]
    conn = client.app.state.repo.conn
    conn.execute(
        """
        insert into company_entities (id, source_id, provider, company_name, credit_code, industry, region, registration_status)
        values ('co_complete', ?, 'tianyan_ai', '宁德时代新能源科技股份有限公司', '91350900587527783P', '电气机械和器材制造业', '福建省', '存续')
        """,
        (source_id,),
    )
    conn.execute(
        """
        insert into company_entities (id, source_id, provider, company_name)
        values ('co_partial', ?, 'tianyan_ai', '宁德时代新能源科技股份有限公司')
        """,
        (source_id,),
    )
    conn.commit()

    res = client.get("/api/admin/companies", params={"q": "宁德时代", "dedupe": True}, auth=("admin", "secret"))

    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["credit_code"] == "91350900587527783P"
