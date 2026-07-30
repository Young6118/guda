from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_db(path: Path | str) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    conn.execute("pragma journal_mode = wal")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists sources (
            id text primary key,
            name text not null,
            platform text not null,
            source_type text not null,
            access_status text not null default 'active',
            provider text,
            acquisition_ladder text not null default '[]',
            preferred_acquisition_layer text,
            max_allowed_acquisition_layer text,
            session_profile_id text,
            auth_profile_id text,
            base_url text,
            query_template text,
            rate_limit_policy text not null default '{}',
            cost_model text not null default '{}',
            coverage_notes text,
            compliance_notes text,
            health_status text not null default 'unknown',
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists topic_packs (
            id text primary key,
            name text not null,
            description text,
            keywords text not null default '[]',
            excluded_keywords text not null default '[]',
            entities text not null default '[]',
            languages text not null default '[]',
            regions text not null default '[]',
            priority integer not null default 0,
            owner text,
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists collection_tasks (
            id text primary key,
            name text not null,
            topic_pack_id text not null references topic_packs(id),
            source_ids text not null,
            query text not null,
            schedule text,
            lookback_window text,
            max_items_per_run integer not null default 10,
            budget_per_run_usd real,
            dedupe_policy text,
            enabled integer not null default 1,
            priority integer not null default 0,
            cursor_json text not null default '{}',
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists collection_runs (
            id text primary key,
            task_id text not null references collection_tasks(id),
            started_at text not null default current_timestamp,
            finished_at text,
            status text not null,
            items_fetched integer not null default 0,
            items_normalized integer not null default 0,
            items_deduped integer not null default 0,
            cost_usd real not null default 0,
            error_summary text,
            run_log_uri text
        );

        create table if not exists rate_policies (
            platform text primary key,
            min_interval_seconds integer not null default 0,
            cooldown_seconds integer not null default 60,
            burst_limit integer not null default 1,
            enabled integer not null default 1,
            last_request_at text,
            cooldown_until text,
            last_error text,
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists raw_items (
            id text primary key,
            source_id text not null references sources(id),
            task_id text not null references collection_tasks(id),
            run_id text not null references collection_runs(id),
            platform_item_id text,
            url text,
            raw_uri text not null,
            raw_sha256 text not null,
            raw_size_bytes integer not null,
            acquisition_layer text not null,
            session_profile_id text,
            content_hash text not null,
            fetched_at text not null
        );
        create unique index if not exists idx_raw_items_content_hash on raw_items(content_hash);

        create table if not exists company_entities (
            id text primary key,
            source_id text references sources(id),
            provider text,
            company_name text not null,
            credit_code text,
            company_id_provider text,
            stock_code text,
            exchange text,
            registration_status text,
            legal_person text,
            industry text,
            region text,
            registration_info_json text not null default '{}',
            risk_snapshot_json text not null default '{}',
            market_profile_json text not null default '{}',
            geo_profile_json text not null default '{}',
            last_enriched_at text,
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists market_observations (
            id text primary key,
            raw_item_id text references raw_items(id),
            source_id text references sources(id),
            provider text,
            company_entity_id text references company_entities(id),
            instrument_code text,
            exchange text,
            observation_type text not null,
            observed_at text,
            period text,
            metrics_json text not null default '{}',
            topics_json text not null default '[]',
            url text,
            created_at text not null default current_timestamp
        );

        create table if not exists geo_entities (
            id text primary key,
            raw_item_id text references raw_items(id),
            source_id text references sources(id),
            provider text,
            company_entity_id text references company_entities(id),
            address_raw text,
            address_normalized text,
            place_id_provider text,
            place_name text,
            place_types text not null default '[]',
            latitude real,
            longitude real,
            viewport_json text not null default '{}',
            region text,
            country_code text,
            rating real,
            review_count integer,
            opening_hours_json text not null default '{}',
            contact_json text not null default '{}',
            distance_matrix_json text not null default '{}',
            directions_json text not null default '{}',
            elevation_meters real,
            last_enriched_at text,
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists session_profiles (
            id text primary key,
            platform text not null,
            profile_name text not null,
            profile_type text not null,
            storage_ref text,
            owner text,
            status text not null default 'active',
            allowed_source_ids text not null default '[]',
            created_at text not null default current_timestamp,
            updated_at text not null default current_timestamp
        );

        create table if not exists evidence_items (
            id text primary key,
            raw_item_id text not null references raw_items(id),
            source_id text not null references sources(id),
            platform text not null,
            item_type text not null,
            author_display text,
            author_id_hash text,
            url text,
            parent_url text,
            title text,
            text text not null,
            language text,
            created_at_source text,
            fetched_at text not null,
            engagement text not null default '{}',
            entities text not null default '[]',
            topics text not null default '[]',
            embedding_id text,
            text_hash text not null,
            near_duplicate_group_id text
        );

        create virtual table if not exists evidence_items_fts using fts5(
            title,
            text,
            content='evidence_items',
            content_rowid='rowid'
        );
        """
    )
    conn.commit()
    seed_default_rate_policies(conn)


def seed_default_rate_policies(conn: sqlite3.Connection) -> None:
    defaults = {
        "arxiv": (3, 300, 1),
        "gdelt": (60, 600, 1),
        "github": (10, 120, 1),
        "hackernews": (2, 60, 1),
        "huggingface": (2, 60, 2),
        "stackexchange": (2, 60, 2),
        "npm": (1, 30, 2),
        "dockerhub": (2, 60, 2),
        "devto": (2, 60, 2),
        "rss": (5, 60, 1),
        "v2ex": (5, 120, 1),
        "baidu_search": (10, 300, 1),
        "tianyan_ai": (10, 300, 1),
        "meta_search": (10, 120, 1),
    }
    for platform, (min_interval, cooldown, burst) in defaults.items():
        conn.execute(
            """
            insert into rate_policies (platform, min_interval_seconds, cooldown_seconds, burst_limit, enabled)
            values (?, ?, ?, ?, 1)
            on conflict(platform) do nothing
            """,
            (platform, min_interval, cooldown, burst),
        )
    conn.commit()
