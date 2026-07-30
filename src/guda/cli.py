from __future__ import annotations

import argparse
import json

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


def main() -> None:
    parser = argparse.ArgumentParser(prog="guda")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db")
    demo = subparsers.add_parser("demo-run")
    demo.add_argument("--query", default="semiconductor supply chain pain points")
    demo.add_argument("--limit", type=int, default=3)
    demo.add_argument("--connector", choices=["meta_search", "v2ex", "tianyan_ai", "github", "rss", "hackernews", "baidu_search", "stackexchange", "npm", "dockerhub", "devto", "gdelt", "huggingface", "arxiv"], default="meta_search")
    args = parser.parse_args()

    settings = Settings()
    conn = connect_db(settings.database_path)
    init_db(conn)
    repo = Repository(conn)

    if args.command == "init-db":
        conn.close()
        print(f"initialized {settings.database_path}")
        return

    if args.command == "demo-run":
        connectors = {
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
        }
        connector = connectors[args.connector]
        source_id = repo.create_source(
            name=connector.name,
            platform=connector.platform,
            source_type="official_api",
            provider=connector.name,
        )
        topic_id = repo.create_topic_pack(name="Semiconductor Watch", description="Semiconductor source intelligence demo")
        task_id = repo.create_collection_task(
            name="Meta Search semiconductor demo",
            topic_pack_id=topic_id,
            source_ids=[source_id],
            query=args.query,
            max_items_per_run=args.limit,
        )
        service = CollectionService(
            repo=repo,
            raw_store=RawStore(settings.raw_dir),
            connectors=connectors,
        )
        result = service.run_task(task_id)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        conn.close()
        return


if __name__ == "__main__":
    main()
