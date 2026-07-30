from __future__ import annotations

from dataclasses import dataclass

from guda.connectors.base import SourceConnector
from guda.repositories import Repository, content_hash
from guda.raw_store import RawStore


@dataclass(frozen=True)
class CollectionResult:
    run_id: str
    status: str
    items_fetched: int
    items_normalized: int


class CollectionService:
    def __init__(self, *, repo: Repository, raw_store: RawStore, connectors: dict[str, SourceConnector]):
        self.repo = repo
        self.raw_store = raw_store
        self.connectors = connectors

    def run_task(self, task_id: str) -> CollectionResult:
        task = self.repo.get_task(task_id)
        run_id = self.repo.start_run(task_id)
        fetched_count = 0
        normalized_count = 0
        try:
            for source_id in task.source_ids:
                source = self.repo.get_source(source_id)
                connector = self.connectors.get(source.platform)
                if connector is None:
                    raise ValueError(f"no connector registered for platform: {source.platform}")
                available, reason = self.repo.is_platform_available(source.platform)
                if not available:
                    continue
                self.repo.mark_platform_request(source.platform)
                try:
                    raw_items = connector.fetch_raw(task.query, task.max_items_per_run)
                except Exception as exc:
                    if "429" in str(exc).lower() or "rate limit" in str(exc).lower() or "rate limited" in str(exc).lower():
                        self.repo.mark_platform_cooldown(source.platform, reason=str(exc))
                    raise
                for raw in raw_items:
                    fetched_count += 1
                    raw_id_for_path = content_hash(source_id, run_id, raw.platform_item_id, raw.url)[:16]
                    metadata = self.raw_store.write(
                        source_id=source_id,
                        run_id=run_id,
                        raw_item_id=raw_id_for_path,
                        payload=raw.payload,
                        fetched_at=raw.fetched_at,
                    )
                    raw_hash = content_hash(source_id, raw.platform_item_id, raw.url, metadata.raw_sha256)
                    raw_item_id = self.repo.insert_raw_item(
                        source_id=source_id,
                        task_id=task_id,
                        run_id=run_id,
                        platform_item_id=raw.platform_item_id,
                        url=raw.url,
                        metadata=metadata,
                        acquisition_layer=connector.acquisition_layer,
                        fetched_at=raw.fetched_at,
                        raw_content_hash=raw_hash,
                    )
                    for draft in connector.normalize(raw):
                        self.repo.insert_evidence(raw_item_id=raw_item_id, source_id=source_id, draft=draft, fetched_at=raw.fetched_at)
                        normalized_count += 1
                    normalize_companies = getattr(connector, "normalize_companies", None)
                    if normalize_companies:
                        for company in normalize_companies(raw):
                            self.repo.insert_company(source_id=source_id, draft=company)
            self.repo.finish_run(run_id, status="completed", items_fetched=fetched_count, items_normalized=normalized_count)
            return CollectionResult(run_id=run_id, status="completed", items_fetched=fetched_count, items_normalized=normalized_count)
        except Exception as exc:
            self.repo.finish_run(run_id, status="failed", items_fetched=fetched_count, items_normalized=normalized_count, error_summary=str(exc))
            raise
