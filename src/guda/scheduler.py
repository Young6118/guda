from __future__ import annotations

import asyncio
import logging

from guda.collection import CollectionService
from guda.repositories import Repository

log = logging.getLogger(__name__)


async def scheduler_loop(repo: Repository, collection: CollectionService, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            for task_id in repo.list_due_tasks():
                try:
                    await asyncio.to_thread(collection.run_task, task_id)
                except Exception:
                    log.exception("scheduled collection failed: %s", task_id)
        except Exception:
            log.exception("scheduler tick failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=30)
        except asyncio.TimeoutError:
            pass
