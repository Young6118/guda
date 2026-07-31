from __future__ import annotations

from pathlib import Path

from guda.db import connect_db, init_db
from guda.repositories import Repository


def test_topic_pack_names_are_reused_and_list_is_deduplicated(tmp_path: Path) -> None:
    conn = connect_db(tmp_path / "app.sqlite")
    init_db(conn)
    repo = Repository(conn)

    first = repo.create_topic_pack(name="Semiconductor Watch", description="first")
    second = repo.create_topic_pack(name=" semiconductor watch ", description="second")

    assert first == second
    assert len(repo.list_topic_packs()) == 1
    assert repo.list_topic_packs()[0]["name"] == "Semiconductor Watch"
