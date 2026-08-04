from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
import secrets

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from guda.collection import CollectionService
from guda.config import Settings
from guda.connectors.arxiv import ArxivConnector
from guda.connectors.baidu_search import BaiduSearchConnector
from guda.connectors.devto import DevToConnector
from guda.connectors.dockerhub import DockerHubConnector
from guda.connectors.gdelt import GDELTConnector
from guda.connectors.github import GitHubConnector
from guda.connectors.hackernews import HackerNewsConnector
from guda.connectors.huggingface import HuggingFaceConnector
from guda.connectors.meta_search import MetaSearchConnector
from guda.connectors.npm_registry import NPMRegistryConnector
from guda.connectors.rss import RSSConnector
from guda.connectors.stackexchange import StackExchangeConnector
from guda.connectors.tianyan_ai import TianyanAIConnector
from guda.connectors.v2ex import V2EXConnector
from guda.db import connect_db, init_db
from guda.raw_store import RawStore
from guda.repositories import Repository
from guda.source_catalog import source_catalog_as_dicts


class SourceCreate(BaseModel):
    name: str
    platform: str
    source_type: str
    provider: str | None = None


class TopicPackCreate(BaseModel):
    name: str
    description: str | None = None


class CollectionTaskCreate(BaseModel):
    name: str
    topic_pack_id: str
    source_ids: list[str]
    query: str
    max_items_per_run: int = 10


class RatePolicyUpdate(BaseModel):
    min_interval_seconds: int
    cooldown_seconds: int
    burst_limit: int = 1
    enabled: bool = True


def _unauthorized() -> Response:
    return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="GUDA Admin"'})


def _basic_auth_ok(request: Request, settings: Settings) -> bool:
    if not settings.admin_username or not settings.admin_password:
        return True
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("basic "):
        return False
    import base64
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return False
    return secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(password, settings.admin_password)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    conn = connect_db(app_settings.database_path)
    init_db(conn)
    repo = Repository(conn)
    collection = CollectionService(
        repo=repo,
        raw_store=RawStore(app_settings.raw_dir),
        connectors={
            "meta_search": MetaSearchConnector(),
            "v2ex": V2EXConnector(),
            "tianyan_ai": TianyanAIConnector(),
            "github": GitHubConnector(),
            "rss": RSSConnector(),
            "hackernews": HackerNewsConnector(),
            "baidu_search": BaiduSearchConnector(),
            "stackexchange": StackExchangeConnector(),
            "npm": NPMRegistryConnector(),
            "dockerhub": DockerHubConnector(),
            "devto": DevToConnector(),
            "gdelt": GDELTConnector(),
            "huggingface": HuggingFaceConnector(),
            "arxiv": ArxivConnector(),
        },
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            conn.close()

    app = FastAPI(title="Global User Data Analysis", version="0.1.0", lifespan=lifespan)
    app.state.repo = repo

    @app.middleware("http")
    async def admin_auth(request: Request, call_next):
        path = request.url.path
        if path.startswith("/admin") or path.startswith("/app") or path.startswith("/api"):
            if not _basic_auth_ok(request, app_settings):
                return _unauthorized()
        return await call_next(request)

    static_dir = Path(__file__).parent / "static" / "admin"
    app.mount("/admin", StaticFiles(directory=static_dir, html=True), name="admin")
    app_dir = Path(__file__).parent / "static" / "app"
    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.is_dir():
        app_dir = frontend_dist
    app.mount("/app", StaticFiles(directory=app_dir, html=True), name="app")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        conn.execute("select 1").fetchone()
        return {"status": "ok", "checks": {"database": "ok"}}

    @app.post("/sources", status_code=status.HTTP_201_CREATED)
    def create_source(payload: SourceCreate) -> dict[str, str]:
        source_id = repo.create_source(
            name=payload.name,
            platform=payload.platform,
            source_type=payload.source_type,
            provider=payload.provider,
        )
        return {"id": source_id}

    @app.get("/sources")
    @app.get("/api/sources")
    def list_sources() -> list[dict[str, Any]]:
        return repo.list_sources()

    @app.get("/source-catalog")
    @app.get("/api/source-catalog")
    def list_source_catalog() -> list[dict[str, str]]:
        return source_catalog_as_dicts()

    @app.get("/rate-policies")
    @app.get("/api/rate-policies")
    def list_rate_policies() -> list[dict[str, Any]]:
        return repo.list_rate_policies()

    @app.get("/api/admin/sources")
    def admin_sources(
        q: str | None = None,
        platform: str | None = None,
        health_status: str | None = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        sort: str = "created_at",
        direction: str = "desc",
    ) -> dict[str, Any]:
        return repo.admin_sources(query=q, platform=platform, health_status=health_status, page=page, page_size=page_size, sort=sort, direction=direction)

    @app.get("/api/admin/rate-policies")
    def admin_rate_policies(
        q: str | None = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        sort: str = "platform",
        direction: str = "asc",
    ) -> dict[str, Any]:
        return repo.admin_rate_policies(query=q, page=page, page_size=page_size, sort=sort, direction=direction)

    @app.get("/api/admin/companies")
    def admin_companies(
        q: str | None = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        dedupe: bool = True,
    ) -> dict[str, Any]:
        return repo.admin_companies(query=q, page=page, page_size=page_size, dedupe=dedupe)

    @app.get("/api/app/overview")
    def app_overview() -> dict[str, Any]:
        return repo.app_overview()

    @app.get("/api/app/analytics")
    def app_analytics(
        q: str | None = None,
        topic_pack_id: str | None = None,
        days: int = Query(default=30, ge=1, le=365),
        limit: int = Query(default=30, ge=1, le=100),
    ) -> dict[str, Any]:
        return repo.app_analytics(query=q, topic_pack_id=topic_pack_id, days=days, limit=limit)

    @app.get("/api/app/insights")
    def app_insights(
        q: str | None = None,
        topic_pack_id: str | None = None,
        days: int = Query(default=30, ge=1, le=365),
        limit: int = Query(default=5, ge=1, le=20),
    ) -> dict[str, Any]:
        return repo.app_insights(query=q, topic_pack_id=topic_pack_id, days=days, limit=limit)

    @app.get("/api/app/report")
    def app_report(
        q: str | None = None,
        topic_pack_id: str | None = None,
        days: int = Query(default=30, ge=1, le=365),
        limit: int = Query(default=10, ge=1, le=50),
    ) -> dict[str, Any]:
        return repo.app_report(query=q, topic_pack_id=topic_pack_id, days=days, limit=limit)

    @app.get("/api/app/quality")
    def app_quality(
        topic_pack_id: str | None = None,
        days: int = Query(default=30, ge=1, le=365),
    ) -> dict[str, Any]:
        return repo.app_quality(topic_pack_id=topic_pack_id, days=days)

    @app.get("/api/app/tasks")
    def app_tasks(topic_pack_id: str | None = None) -> dict[str, Any]:
        return repo.collection_task_monitor(topic_pack_id=topic_pack_id)

    @app.post("/api/app/tasks/{task_id}/run")
    def app_run_task(task_id: str) -> dict[str, Any]:
        try:
            repo.get_task(task_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="collection task not found")
        return collection.run_task(task_id).__dict__

    @app.get("/api/topic-packs")
    def list_topic_packs() -> list[dict[str, Any]]:
        return repo.list_topic_packs()

    @app.get("/api/topic-packs/{topic_pack_id}/dashboard")
    def topic_pack_dashboard(
        topic_pack_id: str,
        from_ts: str | None = None,
        to_ts: str | None = None,
        bucket: str = Query(default="day"),
        limit: int = Query(default=10, ge=1, le=100),
    ) -> dict[str, Any]:
        try:
            return repo.topic_pack_dashboard(topic_pack_id=topic_pack_id, from_ts=from_ts, to_ts=to_ts, bucket=bucket, limit=limit)
        except KeyError:
            raise HTTPException(status_code=404, detail="topic pack not found")

    @app.get("/api/topic-packs/{topic_pack_id}/trends")
    def topic_pack_trends(
        topic_pack_id: str,
        from_ts: str | None = None,
        to_ts: str | None = None,
        bucket: str = Query(default="day"),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        try:
            return repo.topic_pack_trends(topic_pack_id=topic_pack_id, from_ts=from_ts, to_ts=to_ts, bucket=bucket, limit=limit)
        except KeyError:
            raise HTTPException(status_code=404, detail="topic pack not found")

    @app.get("/api/app/evidence")
    def app_evidence(
        q: str | None = None,
        platform: str | None = None,
        item_type: str | None = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        return repo.app_evidence(query=q, platform=platform, item_type=item_type, page=page, page_size=page_size)

    @app.get("/api/evidence-items")
    def list_evidence_items(
        q: str | None = None,
        platform: str | None = None,
        item_type: str | None = None,
        language: str | None = None,
        source_id: str | None = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        sort: str = "fetched_at",
        direction: str = "desc",
    ) -> dict[str, Any]:
        return repo.evidence_items(query=q, platform=platform, item_type=item_type, language=language, source_id=source_id, page=page, page_size=page_size, sort=sort, direction=direction)

    @app.get("/api/evidence-items/{evidence_id}")
    def get_evidence_item(evidence_id: str) -> dict[str, Any]:
        item = repo.get_evidence_item(evidence_id)
        if item is None:
            raise HTTPException(status_code=404, detail="evidence item not found")
        return item

    @app.get("/api/evidence/facets")
    def evidence_facets() -> dict[str, list[dict[str, Any]]]:
        return repo.evidence_facets()

    @app.put("/rate-policies/{platform}")
    @app.put("/api/rate-policies/{platform}")
    def update_rate_policy(platform: str, payload: RatePolicyUpdate) -> dict[str, Any]:
        return repo.upsert_rate_policy(
            platform=platform,
            min_interval_seconds=payload.min_interval_seconds,
            cooldown_seconds=payload.cooldown_seconds,
            burst_limit=payload.burst_limit,
            enabled=payload.enabled,
        )

    @app.post("/rate-policies/{platform}/clear-cooldown")
    @app.post("/api/rate-policies/{platform}/clear-cooldown")
    def clear_rate_policy_cooldown(platform: str) -> dict[str, Any] | None:
        return repo.clear_platform_cooldown(platform)

    @app.post("/sources/{source_id}/test")
    def test_source(source_id: str) -> dict[str, Any]:
        source = repo.get_source(source_id)
        connector = collection.connectors.get(source.platform)
        if connector is None:
            repo.update_source_health(source_id, "error")
            return {"id": source_id, "ok": False, "health_status": "error", "error": f"no connector registered for platform: {source.platform}"}
        try:
            ok = bool(connector.test_connection())
        except Exception as exc:
            repo.update_source_health(source_id, "error")
            return {"id": source_id, "ok": False, "health_status": "error", "error": str(exc)}
        health_status = "ok" if ok else "error"
        repo.update_source_health(source_id, health_status)
        return {"id": source_id, "ok": ok, "health_status": health_status, "error": None}

    @app.get("/evidence/search")
    @app.get("/api/evidence/search")
    def search_evidence(
        query: str = Query(min_length=1),
        platform: str | None = None,
        item_type: str | None = None,
        limit: int = Query(default=20, ge=1, le=100),
    ) -> list[dict[str, Any]]:
        return repo.search_evidence(query=query, platform=platform, item_type=item_type, limit=limit)

    @app.get("/companies/search")
    @app.get("/api/companies/search")
    def search_companies(query: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
        return repo.search_companies(query=query, limit=limit)

    @app.post("/topic-packs", status_code=status.HTTP_201_CREATED)
    def create_topic_pack(payload: TopicPackCreate) -> dict[str, str]:
        topic_id = repo.create_topic_pack(name=payload.name, description=payload.description)
        return {"id": topic_id}

    @app.post("/collection-tasks", status_code=status.HTTP_201_CREATED)
    def create_collection_task(payload: CollectionTaskCreate) -> dict[str, str]:
        task_id = repo.create_collection_task(
            name=payload.name,
            topic_pack_id=payload.topic_pack_id,
            source_ids=payload.source_ids,
            query=payload.query,
            max_items_per_run=payload.max_items_per_run,
        )
        return {"id": task_id}

    @app.post("/collection-tasks/{task_id}/run")
    @app.post("/api/collection-tasks/{task_id}/run")
    def run_collection_task(task_id: str) -> dict[str, Any]:
        result = collection.run_task(task_id)
        return result.__dict__

    return app


app = create_app()
