from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from guda.connectors.base import CompanyDraft, EvidenceDraft
from guda.raw_store import RawMetadata


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def content_hash(*parts: str | None) -> str:
    payload = "\u001f".join(part or "" for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def page_result(items: list[dict[str, Any]], *, total: int, page: int, page_size: int) -> dict[str, Any]:
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def clamp_page(page: int, page_size: int) -> tuple[int, int, int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return page, page_size, (page - 1) * page_size


def like_query(query: str | None) -> str:
    return f"%{query or ''}%"


@dataclass(frozen=True)
class TaskRecord:
    id: str
    name: str
    topic_pack_id: str
    source_ids: list[str]
    query: str
    max_items_per_run: int


@dataclass(frozen=True)
class SourceRecord:
    id: str
    name: str
    platform: str
    source_type: str


class Repository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_source(self, *, name: str, platform: str, source_type: str, provider: str | None = None) -> str:
        source_id = new_id("src")
        self.conn.execute(
            """
            insert into sources (id, name, platform, source_type, provider, acquisition_ladder)
            values (?, ?, ?, ?, ?, ?)
            """,
            (source_id, name, platform, source_type, provider, json_dumps([source_type])),
        )
        self.conn.commit()
        return source_id

    def list_sources(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "select id, name, platform, source_type, access_status, provider, health_status from sources order by created_at"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_source(self, source_id: str) -> SourceRecord:
        row = self.conn.execute(
            "select id, name, platform, source_type from sources where id = ?", (source_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"source not found: {source_id}")
        return SourceRecord(id=row["id"], name=row["name"], platform=row["platform"], source_type=row["source_type"])

    def update_source_health(self, source_id: str, health_status: str) -> None:
        self.conn.execute(
            "update sources set health_status = ?, updated_at = ? where id = ?",
            (health_status, utc_now(), source_id),
        )
        self.conn.commit()

    def list_rate_policies(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            select platform, min_interval_seconds, cooldown_seconds, burst_limit, enabled,
                   last_request_at, cooldown_until, last_error, updated_at
            from rate_policies
            order by platform
            """
        ).fetchall()
        return [self._policy_dict(row) for row in rows]

    def get_rate_policy(self, platform: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            select platform, min_interval_seconds, cooldown_seconds, burst_limit, enabled,
                   last_request_at, cooldown_until, last_error, updated_at
            from rate_policies where platform = ?
            """,
            (platform,),
        ).fetchone()
        return self._policy_dict(row) if row else None

    def upsert_rate_policy(
        self,
        *,
        platform: str,
        min_interval_seconds: int,
        cooldown_seconds: int,
        burst_limit: int,
        enabled: bool,
    ) -> dict[str, Any]:
        self.conn.execute(
            """
            insert into rate_policies (platform, min_interval_seconds, cooldown_seconds, burst_limit, enabled, updated_at)
            values (?, ?, ?, ?, ?, ?)
            on conflict(platform) do update set
                min_interval_seconds = excluded.min_interval_seconds,
                cooldown_seconds = excluded.cooldown_seconds,
                burst_limit = excluded.burst_limit,
                enabled = excluded.enabled,
                updated_at = excluded.updated_at
            """,
            (platform, min_interval_seconds, cooldown_seconds, burst_limit, int(enabled), utc_now()),
        )
        self.conn.commit()
        policy = self.get_rate_policy(platform)
        if policy is None:
            raise RuntimeError(f"rate policy not found after upsert: {platform}")
        return policy

    def is_platform_available(self, platform: str) -> tuple[bool, str | None]:
        policy = self.get_rate_policy(platform)
        if policy is None or not policy["enabled"]:
            return True, None
        now = datetime.now(timezone.utc)
        cooldown_until = self._parse_utc(policy.get("cooldown_until"))
        if cooldown_until and cooldown_until > now:
            return False, f"cooling down until {policy['cooldown_until']}"
        last_request_at = self._parse_utc(policy.get("last_request_at"))
        if last_request_at:
            next_allowed = last_request_at + timedelta(seconds=int(policy["min_interval_seconds"]))
            if next_allowed > now:
                return False, f"rate limited until {next_allowed.isoformat().replace('+00:00', 'Z')}"
        return True, None

    def mark_platform_request(self, platform: str) -> None:
        self.conn.execute(
            """
            insert into rate_policies (platform, last_request_at, updated_at)
            values (?, ?, ?)
            on conflict(platform) do update set last_request_at = excluded.last_request_at, updated_at = excluded.updated_at
            """,
            (platform, utc_now(), utc_now()),
        )
        self.conn.commit()

    def mark_platform_cooldown(self, platform: str, *, reason: str) -> None:
        policy = self.get_rate_policy(platform)
        cooldown_seconds = int(policy["cooldown_seconds"]) if policy else 60
        until = (datetime.now(timezone.utc) + timedelta(seconds=cooldown_seconds)).isoformat().replace("+00:00", "Z")
        now = utc_now()
        self.conn.execute(
            """
            insert into rate_policies (platform, cooldown_until, last_error, updated_at)
            values (?, ?, ?, ?)
            on conflict(platform) do update set
                cooldown_until = excluded.cooldown_until,
                last_error = excluded.last_error,
                updated_at = excluded.updated_at
            """,
            (platform, until, reason, now),
        )
        self.conn.commit()

    def clear_platform_cooldown(self, platform: str) -> dict[str, Any] | None:
        self.conn.execute(
            "update rate_policies set cooldown_until = null, last_error = null, updated_at = ? where platform = ?",
            (utc_now(), platform),
        )
        self.conn.commit()
        return self.get_rate_policy(platform)

    @staticmethod
    def _parse_utc(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _policy_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["enabled"] = bool(data["enabled"])
        return data

    def create_topic_pack(self, *, name: str, description: str | None = None) -> str:
        topic_id = new_id("topic")
        self.conn.execute(
            "insert into topic_packs (id, name, description) values (?, ?, ?)",
            (topic_id, name, description),
        )
        self.conn.commit()
        return topic_id

    def list_topic_packs(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "select id, name, description, keywords, entities, languages, regions, priority, owner, created_at, updated_at from topic_packs order by priority desc, created_at desc"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_topic_pack(self, topic_pack_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "select id, name, description, keywords, entities, languages, regions, priority, owner, created_at, updated_at from topic_packs where id = ?",
            (topic_pack_id,),
        ).fetchone()
        return dict(row) if row else None

    def topic_pack_dashboard(self, *, topic_pack_id: str, from_ts: str | None = None, to_ts: str | None = None, bucket: str = "day", limit: int = 10) -> dict[str, Any]:
        topic_pack = self.get_topic_pack(topic_pack_id)
        if topic_pack is None:
            raise KeyError(f"topic pack not found: {topic_pack_id}")
        task_rows = self.conn.execute(
            "select id from collection_tasks where topic_pack_id = ?",
            (topic_pack_id,),
        ).fetchall()
        task_ids = [row["id"] for row in task_rows]
        if not task_ids:
            return {
                "topic_pack": topic_pack,
                "summary": {"evidence_count": 0, "source_count": 0, "platform_count": 0, "company_count": 0, "first_seen_at": None, "last_seen_at": None},
                "timeline": [],
                "source_coverage": [],
                "rising_entities": [],
                "representative_evidence": [],
            }
        placeholders = ",".join("?" for _ in task_ids)
        evidence_where = [f"ri.task_id in ({placeholders})"]
        params: list[Any] = list(task_ids)
        if from_ts:
            evidence_where.append("coalesce(e.created_at_source, e.fetched_at) >= ?")
            params.append(from_ts)
        if to_ts:
            evidence_where.append("coalesce(e.created_at_source, e.fetched_at) <= ?")
            params.append(to_ts)
        where_sql = " and ".join(evidence_where)
        evidence_rows = self.conn.execute(
            f"""
            select e.id, e.platform, e.item_type, e.title, e.text, e.url, e.fetched_at, e.created_at_source,
                   e.language, e.engagement, e.entities, e.topics, e.text_hash, s.id as source_id, s.name as source_name
            from raw_items ri
            join evidence_items e on e.raw_item_id = ri.id
            join sources s on s.id = e.source_id
            where {where_sql}
            order by coalesce(e.created_at_source, e.fetched_at) desc, e.fetched_at desc
            """,
            params,
        ).fetchall()
        evidence = [dict(row) for row in evidence_rows]
        source_ids = {row["source_id"] for row in evidence_rows}
        platforms = {row["platform"] for row in evidence_rows}
        companies = self.conn.execute(
            f"""
            select count(distinct ce.id)
            from raw_items ri
            join evidence_items e on e.raw_item_id = ri.id
            join company_entities ce on ce.source_id = e.source_id
            where {where_sql}
            """,
            params,
        ).fetchone()[0]
        timeline = self._topic_pack_timeline(evidence, bucket=bucket)
        source_coverage = self._topic_pack_source_coverage(evidence, limit=limit)
        rising_entities = self._topic_pack_rising_entities(evidence, limit=limit)
        representative_evidence = self._topic_pack_representative_evidence(evidence, limit=limit)
        first_seen = min((row["created_at_source"] or row["fetched_at"] for row in evidence_rows), default=None)
        last_seen = max((row["created_at_source"] or row["fetched_at"] for row in evidence_rows), default=None)
        return {
            "topic_pack": topic_pack,
            "summary": {
                "evidence_count": len(evidence_rows),
                "source_count": len(source_ids),
                "platform_count": len(platforms),
                "company_count": companies,
                "first_seen_at": first_seen,
                "last_seen_at": last_seen,
            },
            "timeline": timeline,
            "source_coverage": source_coverage,
            "rising_entities": rising_entities,
            "representative_evidence": representative_evidence,
        }

    def topic_pack_trends(self, *, topic_pack_id: str, from_ts: str | None = None, to_ts: str | None = None, bucket: str = "day", limit: int = 20) -> dict[str, Any]:
        dashboard = self.topic_pack_dashboard(topic_pack_id=topic_pack_id, from_ts=from_ts, to_ts=to_ts, bucket=bucket, limit=limit)
        timeline = dashboard["timeline"]
        platform_counts: dict[str, int] = {}
        for row in dashboard["source_coverage"]:
            platform_counts[row["platform"]] = platform_counts.get(row["platform"], 0) + row["evidence_count"]
        return {
            "topic_pack": dashboard["topic_pack"],
            "range": {"from": from_ts, "to": to_ts, "bucket": bucket},
            "volume": timeline,
            "platforms": [{"platform": key, "evidence_count": value} for key, value in sorted(platform_counts.items(), key=lambda pair: (-pair[1], pair[0]))],
            "rising_entities": dashboard["rising_entities"][:limit],
            "source_coverage": dashboard["source_coverage"][:limit],
        }

    def _topic_pack_timeline(self, evidence: list[dict[str, Any]], *, bucket: str) -> list[dict[str, Any]]:
        counts: dict[str, dict[str, Any]] = {}
        for row in evidence:
            stamp = row.get("created_at_source") or row.get("fetched_at")
            if not stamp:
                continue
            key = stamp[:10] if bucket == "day" else stamp[:7]
            entry = counts.setdefault(key, {"bucket": key, "evidence_count": 0, "source_ids": set()})
            entry["evidence_count"] += 1
            entry["source_ids"].add(row["source_id"])
        out = []
        for key in sorted(counts):
            entry = counts[key]
            out.append({"bucket": key, "evidence_count": entry["evidence_count"], "source_count": len(entry["source_ids"])})
        return out

    def _topic_pack_source_coverage(self, evidence: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
        coverage: dict[str, dict[str, Any]] = {}
        for row in evidence:
            entry = coverage.setdefault(row["source_id"], {"source_id": row["source_id"], "source_name": row["source_name"], "platform": row["platform"], "evidence_count": 0, "latest_fetched_at": row["fetched_at"]})
            entry["evidence_count"] += 1
            if row["fetched_at"] > entry["latest_fetched_at"]:
                entry["latest_fetched_at"] = row["fetched_at"]
        return sorted(coverage.values(), key=lambda row: (-row["evidence_count"], row["source_name"]))[:limit]

    def _topic_pack_rising_entities(self, evidence: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
        midpoint = max(len(evidence) // 2, 1)
        recent = evidence[:midpoint]
        prior = evidence[midpoint:midpoint * 2]
        def count_entities(rows: list[dict[str, Any]]) -> dict[str, int]:
            counts: dict[str, int] = {}
            for row in rows:
                for entity in json.loads(row.get("entities") or "[]"):
                    counts[entity] = counts.get(entity, 0) + 1
            return counts
        recent_counts = count_entities(recent)
        prior_counts = count_entities(prior)
        out = []
        for entity, count in sorted(recent_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            previous = prior_counts.get(entity, 0)
            out.append({"entity": entity, "evidence_count": count, "previous_count": previous, "velocity_score": round(count / max(previous, 1), 2)})
        return out[:limit]

    def _topic_pack_representative_evidence(self, evidence: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
        seen: set[str] = set()
        out = []
        for row in evidence:
            if row["text_hash"] in seen:
                continue
            seen.add(row["text_hash"])
            out.append({"id": row["id"], "title": row["title"], "url": row["url"], "platform": row["platform"], "item_type": row["item_type"], "fetched_at": row["fetched_at"], "source_name": row["source_name"]})
            if len(out) >= limit:
                break
        return out

    def create_collection_task(
        self,
        *,
        name: str,
        topic_pack_id: str,
        source_ids: list[str],
        query: str,
        max_items_per_run: int = 10,
    ) -> str:
        task_id = new_id("task")
        self.conn.execute(
            """
            insert into collection_tasks (id, name, topic_pack_id, source_ids, query, max_items_per_run)
            values (?, ?, ?, ?, ?, ?)
            """,
            (task_id, name, topic_pack_id, json_dumps(source_ids), query, max_items_per_run),
        )
        self.conn.commit()
        return task_id

    def get_task(self, task_id: str) -> TaskRecord:
        row = self.conn.execute(
            "select id, name, topic_pack_id, source_ids, query, max_items_per_run from collection_tasks where id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"collection task not found: {task_id}")
        return TaskRecord(
            id=row["id"],
            name=row["name"],
            topic_pack_id=row["topic_pack_id"],
            source_ids=json.loads(row["source_ids"]),
            query=row["query"],
            max_items_per_run=row["max_items_per_run"],
        )

    def start_run(self, task_id: str) -> str:
        run_id = new_id("run")
        self.conn.execute(
            "insert into collection_runs (id, task_id, status, started_at) values (?, ?, 'running', ?)",
            (run_id, task_id, utc_now()),
        )
        self.conn.commit()
        return run_id

    def finish_run(self, run_id: str, *, status: str, items_fetched: int, items_normalized: int, error_summary: str | None = None) -> None:
        self.conn.execute(
            """
            update collection_runs
            set status = ?, items_fetched = ?, items_normalized = ?, finished_at = ?, error_summary = ?
            where id = ?
            """,
            (status, items_fetched, items_normalized, utc_now(), error_summary, run_id),
        )
        self.conn.commit()

    def insert_raw_item(
        self,
        *,
        source_id: str,
        task_id: str,
        run_id: str,
        platform_item_id: str | None,
        url: str | None,
        metadata: RawMetadata,
        acquisition_layer: str,
        fetched_at: str,
        raw_content_hash: str,
    ) -> str:
        raw_item_id = new_id("raw")
        self.conn.execute(
            """
            insert into raw_items (
                id, source_id, task_id, run_id, platform_item_id, url, raw_uri,
                raw_sha256, raw_size_bytes, acquisition_layer, content_hash, fetched_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_item_id,
                source_id,
                task_id,
                run_id,
                platform_item_id,
                url,
                metadata.raw_uri,
                metadata.raw_sha256,
                metadata.raw_size_bytes,
                acquisition_layer,
                raw_content_hash,
                fetched_at,
            ),
        )
        self.conn.commit()
        return raw_item_id

    def insert_evidence(self, *, raw_item_id: str, source_id: str, draft: EvidenceDraft, fetched_at: str) -> str:
        evidence_id = new_id("evi")
        text_hash = content_hash(draft.platform, draft.item_type, draft.url, draft.title, draft.text)
        self.conn.execute(
            """
            insert into evidence_items (
                id, raw_item_id, source_id, platform, item_type, author_display,
                url, parent_url, title, text, language, created_at_source, fetched_at,
                engagement, entities, topics, text_hash
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                raw_item_id,
                source_id,
                draft.platform,
                draft.item_type,
                draft.author_display,
                draft.url,
                draft.parent_url,
                draft.title,
                draft.text,
                draft.language,
                draft.created_at_source,
                fetched_at,
                json_dumps(draft.engagement),
                json_dumps(draft.entities),
                json_dumps(draft.topics),
                text_hash,
            ),
        )
        self.conn.execute(
            "insert into evidence_items_fts(rowid, title, text) values (last_insert_rowid(), ?, ?)",
            (draft.title or "", draft.text),
        )
        self.conn.commit()
        return evidence_id

    def insert_company(self, *, source_id: str, draft: CompanyDraft) -> str:
        company_id = new_id("co")
        self.conn.execute(
            """
            insert into company_entities (
                id, source_id, provider, company_name, credit_code, company_id_provider,
                stock_code, exchange, registration_status, legal_person, industry, region,
                registration_info_json, risk_snapshot_json, market_profile_json, geo_profile_json,
                last_enriched_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                source_id,
                draft.provider,
                draft.company_name,
                draft.credit_code,
                draft.company_id_provider,
                draft.stock_code,
                draft.exchange,
                draft.registration_status,
                draft.legal_person,
                draft.industry,
                draft.region,
                json_dumps(draft.registration_info),
                json_dumps(draft.risk_snapshot),
                json_dumps(draft.market_profile),
                json_dumps(draft.geo_profile),
                utc_now(),
            ),
        )
        self.conn.commit()
        return company_id

    def search_evidence(
        self,
        *,
        query: str,
        platform: str | None = None,
        item_type: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        clauses = ["evidence_items_fts match ?"]
        params: list[Any] = [query]
        if platform:
            clauses.append("e.platform = ?")
            params.append(platform)
        if item_type:
            clauses.append("e.item_type = ?")
            params.append(item_type)
        params.append(limit)
        rows = self.conn.execute(
            f"""
            select
                e.id, e.platform, e.item_type, e.title, e.text, e.url, e.fetched_at,
                e.source_id, s.name as source_name,
                snippet(evidence_items_fts, 1, '[', ']', ' ... ', 24) as snippet
            from evidence_items_fts
            join evidence_items e on e.rowid = evidence_items_fts.rowid
            join sources s on s.id = e.source_id
            where {' and '.join(clauses)}
            order by rank
            limit ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]

    def search_companies(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        like = f"%{query}%"
        rows = self.conn.execute(
            """
            select
                id, source_id, provider, company_name, credit_code, company_id_provider,
                stock_code, exchange, registration_status, legal_person, industry, region,
                last_enriched_at
            from company_entities
            where company_name like ?
               or coalesce(credit_code, '') like ?
               or coalesce(industry, '') like ?
               or coalesce(region, '') like ?
            order by last_enriched_at desc, created_at desc
            limit ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def admin_sources(self, *, query: str | None, platform: str | None, health_status: str | None, page: int, page_size: int, sort: str, direction: str) -> dict[str, Any]:
        page, page_size, offset = clamp_page(page, page_size)
        sortable = {"name": "name", "platform": "platform", "health_status": "health_status", "created_at": "created_at"}
        order = sortable.get(sort, "created_at")
        direction_sql = "desc" if direction.lower() == "desc" else "asc"
        clauses = ["(name like ? or platform like ? or source_type like ? or coalesce(provider, '') like ? or health_status like ?)"]
        params: list[Any] = [like_query(query)] * 5
        if platform:
            clauses.append("platform = ?")
            params.append(platform)
        if health_status:
            clauses.append("health_status = ?")
            params.append(health_status)
        where = " and ".join(clauses)
        total = self.conn.execute(f"select count(*) from sources where {where}", params).fetchone()[0]
        rows = self.conn.execute(
            f"""
            select id, name, platform, source_type, access_status, provider, health_status, created_at, updated_at
            from sources
            where {where}
            order by {order} {direction_sql}
            limit ? offset ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        return page_result([dict(row) for row in rows], total=total, page=page, page_size=page_size)

    def admin_rate_policies(self, *, query: str | None, page: int, page_size: int, sort: str, direction: str) -> dict[str, Any]:
        page, page_size, offset = clamp_page(page, page_size)
        sortable = {"platform": "platform", "min_interval_seconds": "min_interval_seconds", "cooldown_seconds": "cooldown_seconds", "updated_at": "updated_at"}
        order = sortable.get(sort, "platform")
        direction_sql = "desc" if direction.lower() == "desc" else "asc"
        params: list[Any] = [like_query(query), like_query(query)]
        total = self.conn.execute("select count(*) from rate_policies where platform like ? or coalesce(last_error, '') like ?", params).fetchone()[0]
        rows = self.conn.execute(
            f"""
            select platform, min_interval_seconds, cooldown_seconds, burst_limit, enabled,
                   last_request_at, cooldown_until, last_error, updated_at
            from rate_policies
            where platform like ? or coalesce(last_error, '') like ?
            order by {order} {direction_sql}
            limit ? offset ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        return page_result([self._policy_dict(row) for row in rows], total=total, page=page, page_size=page_size)

    def admin_companies(self, *, query: str | None, page: int, page_size: int, dedupe: bool = True) -> dict[str, Any]:
        page, page_size, offset = clamp_page(page, page_size)
        q = like_query(query)
        where = "company_name like ? or coalesce(credit_code, '') like ? or coalesce(industry, '') like ? or coalesce(region, '') like ?"
        if dedupe:
            rows = self.conn.execute(
                f"""
                with ranked as (
                    select *,
                           row_number() over (
                               partition by company_name
                               order by
                                   case when credit_code is not null and credit_code != '' then 0 else 1 end,
                                   case when industry is not null and industry != '' then 0 else 1 end,
                                   updated_at desc
                           ) as rn
                    from company_entities
                    where {where}
                )
                select id, source_id, provider, company_name, credit_code, company_id_provider,
                       stock_code, exchange, registration_status, legal_person, industry, region, last_enriched_at
                from ranked
                where rn = 1
                order by last_enriched_at desc, company_name asc
                limit ? offset ?
                """,
                (q, q, q, q, page_size, offset),
            ).fetchall()
            total = self.conn.execute(
                f"""
                with ranked as (
                    select row_number() over (partition by company_name order by updated_at desc) as rn
                    from company_entities
                    where {where}
                ) select count(*) from ranked where rn = 1
                """,
                (q, q, q, q),
            ).fetchone()[0]
        else:
            total = self.conn.execute(f"select count(*) from company_entities where {where}", (q, q, q, q)).fetchone()[0]
            rows = self.conn.execute(
                f"""
                select id, source_id, provider, company_name, credit_code, company_id_provider,
                       stock_code, exchange, registration_status, legal_person, industry, region, last_enriched_at
                from company_entities
                where {where}
                order by last_enriched_at desc, company_name asc
                limit ? offset ?
                """,
                (q, q, q, q, page_size, offset),
            ).fetchall()
        return page_result([dict(row) for row in rows], total=total, page=page, page_size=page_size)

    def app_overview(self) -> dict[str, Any]:
        metrics = {
            "sources": self.conn.execute("select count(*) from sources").fetchone()[0],
            "evidence_items": self.conn.execute("select count(*) from evidence_items").fetchone()[0],
            "companies": self.conn.execute("select count(*) from company_entities").fetchone()[0],
            "collection_runs": self.conn.execute("select count(*) from collection_runs").fetchone()[0],
        }
        platforms = [dict(row) for row in self.conn.execute("""
            select platform, count(*) as evidence_count, max(fetched_at) as latest_fetched_at
            from evidence_items
            group by platform
            order by evidence_count desc, platform asc
            limit 12
        """).fetchall()]
        recent = [dict(row) for row in self.conn.execute("""
            select e.id, e.platform, e.item_type, e.title, e.url, e.fetched_at, s.name as source_name
            from evidence_items e
            join sources s on s.id = e.source_id
            order by e.fetched_at desc
            limit 10
        """).fetchall()]
        return {"metrics": metrics, "platforms": platforms, "recent_evidence": recent}

    def app_evidence(self, *, query: str | None, platform: str | None, item_type: str | None, page: int, page_size: int) -> dict[str, Any]:
        return self.evidence_items(query=query, platform=platform, item_type=item_type, language=None, source_id=None, page=page, page_size=page_size, sort="fetched_at", direction="desc")

    def evidence_items(
        self,
        *,
        query: str | None,
        platform: str | None,
        item_type: str | None,
        language: str | None,
        source_id: str | None,
        page: int,
        page_size: int,
        sort: str,
        direction: str,
    ) -> dict[str, Any]:
        page, page_size, offset = clamp_page(page, page_size)
        sortable = {
            "fetched_at": "e.fetched_at",
            "created_at_source": "e.created_at_source",
            "platform": "e.platform",
            "item_type": "e.item_type",
        }
        order = sortable.get(sort, "e.fetched_at")
        direction_sql = "asc" if direction.lower() == "asc" else "desc"
        clauses: list[str] = []
        params: list[Any] = []
        if query:
            clauses.append("(e.title like ? or e.text like ? or e.platform like ? or e.item_type like ?)")
            params.extend([like_query(query)] * 4)
        if platform:
            clauses.append("e.platform = ?")
            params.append(platform)
        if item_type:
            clauses.append("e.item_type = ?")
            params.append(item_type)
        if language:
            clauses.append("e.language = ?")
            params.append(language)
        if source_id:
            clauses.append("e.source_id = ?")
            params.append(source_id)
        where = " where " + " and ".join(clauses) if clauses else ""
        total = self.conn.execute(f"select count(*) from evidence_items e{where}", params).fetchone()[0]
        rows = self.conn.execute(
            f"""
            select e.id, e.platform, e.item_type, e.title, e.text, e.url, e.fetched_at,
                   e.created_at_source, e.language, e.engagement, e.entities, e.topics, e.text_hash,
                   s.id as source_id, s.name as source_name, s.platform as source_platform
            from evidence_items e
            join sources s on s.id = e.source_id
            {where}
            order by {order} {direction_sql}, e.id asc
            limit ? offset ?
            """,
            [*params, page_size, offset],
        ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            text = item.pop("text") or ""
            item["snippet"] = text[:240]
            item["source"] = {"id": item.pop("source_id"), "name": item.pop("source_name"), "platform": item.pop("source_platform")}
            items.append(item)
        return page_result(items, total=total, page=page, page_size=page_size)

    def get_evidence_item(self, evidence_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            select e.*, s.name as source_name, s.platform as source_platform
            from evidence_items e
            join sources s on s.id = e.source_id
            where e.id = ?
            """,
            (evidence_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["source"] = {"id": data["source_id"], "name": data.pop("source_name"), "platform": data.pop("source_platform")}
        data["citations"] = {"url": data.get("url"), "raw_item_id": data.get("raw_item_id")}
        return data

    def evidence_facets(self) -> dict[str, list[dict[str, Any]]]:
        def grouped(column: str) -> list[dict[str, Any]]:
            rows = self.conn.execute(
                f"""
                select {column} as value, count(*) as count
                from evidence_items
                where {column} is not null and {column} != ''
                group by {column}
                order by count desc, value asc
                """
            ).fetchall()
            return [dict(row) for row in rows]

        sources = self.conn.execute(
            """
            select s.id, s.name, s.platform, count(e.id) as count
            from sources s
            join evidence_items e on e.source_id = s.id
            group by s.id, s.name, s.platform
            order by count desc, s.name asc
            """
        ).fetchall()
        return {
            "platforms": grouped("platform"),
            "item_types": grouped("item_type"),
            "languages": grouped("language"),
            "sources": [dict(row) for row in sources],
        }
