from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from guda.config import Settings
from guda.db import connect_db, init_db
from guda.raw_store import RawStore


def test_init_db_creates_core_tables(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data", database_path=tmp_path / "data" / "app.sqlite")

    conn = connect_db(settings.database_path)
    init_db(conn)

    table_names = {
        row[0]
        for row in conn.execute("select name from sqlite_master where type in ('table', 'view')")
    }

    assert {
        "sources",
        "topic_packs",
        "collection_tasks",
        "collection_runs",
        "raw_items",
        "evidence_items",
        "company_entities",
        "market_observations",
        "geo_entities",
        "session_profiles",
        "evidence_items_fts",
    }.issubset(table_names)


def test_raw_store_writes_canonical_json_and_returns_integrity_metadata(tmp_path: Path) -> None:
    store = RawStore(tmp_path / "data" / "raw")

    metadata = store.write(
        source_id="src_meta_search",
        run_id="run_001",
        raw_item_id="raw_001",
        payload={"b": 2, "a": 1},
        fetched_at="2026-07-30T00:00:00Z",
    )

    raw_path = tmp_path / "data" / metadata.raw_uri
    assert raw_path.exists()
    assert metadata.raw_size_bytes > 0
    assert len(metadata.raw_sha256) == 64
    assert json.loads(raw_path.read_text()) == {"a": 1, "b": 2}
    assert metadata.raw_uri.startswith("raw/src_meta_search/2026/07/30/run_001/raw_001.json")


def test_sqlite_foreign_keys_are_enabled(tmp_path: Path) -> None:
    db_path = tmp_path / "app.sqlite"
    conn = connect_db(db_path)
    init_db(conn)

    try:
        conn.execute(
            """
            insert into collection_tasks (id, name, topic_pack_id, source_ids, query)
            values ('task_missing_topic', 'bad', 'missing_topic', '[]', 'x')
            """
        )
    except sqlite3.IntegrityError:
        pass
    else:
        raise AssertionError("foreign key violation should fail")
