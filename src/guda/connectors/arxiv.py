from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class ArxivConnector:
    name = "arxiv"
    platform = "arxiv"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(base_url="https://export.arxiv.org", timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"})

    def test_connection(self) -> bool:
        response = self.client.get("/api/query", params={"search_query": "all:test", "max_results": 1})
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        response = self.client.get("/api/query", params={"search_query": f"all:{query}", "max_results": limit, "sortBy": "submittedDate", "sortOrder": "descending"})
        if response.status_code == 429:
            raise RuntimeError("arXiv rate limited this request; retry after a few seconds and keep cadence near one request per three seconds")
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return [self._envelope(entry, fetched_at) for entry in self._entries(response.text)[:limit]]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        paper = raw.payload.get("paper", {})
        return [EvidenceDraft(platform="arxiv", item_type="paper", url=raw.url, title=raw.title, text=paper.get("summary") or raw.title or "", author_display=", ".join(paper.get("authors") or []), created_at_source=paper.get("published"), engagement={"updated": paper.get("updated"), "primary_category": paper.get("primary_category"), "pdf_url": paper.get("pdf_url")}, topics=paper.get("categories") or [])]

    def _entries(self, xml_text: str) -> list[dict[str, Any]]:
        ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = ET.fromstring(xml_text)
        papers = []
        for entry in root.findall("a:entry", ns):
            raw_id = self._text(entry, "a:id", ns) or ""
            arxiv_id = raw_id.rsplit("/abs/", 1)[-1]
            pdf = None
            for link in entry.findall("a:link", ns):
                if link.get("title") == "pdf" or (link.get("href") or "").endswith(".pdf"):
                    pdf = link.get("href")
            primary = entry.find("arxiv:primary_category", ns)
            papers.append({
                "id": arxiv_id,
                "url": raw_id.replace("http://", "https://"),
                "title": (self._text(entry, "a:title", ns) or "").replace("\n", " ").strip(),
                "summary": (self._text(entry, "a:summary", ns) or "").replace("\n", " ").strip(),
                "authors": [self._text(author, "a:name", ns) for author in entry.findall("a:author", ns) if self._text(author, "a:name", ns)],
                "published": self._text(entry, "a:published", ns),
                "updated": self._text(entry, "a:updated", ns),
                "primary_category": primary.get("term") if primary is not None else None,
                "categories": [cat.get("term") for cat in entry.findall("a:category", ns) if cat.get("term")],
                "pdf_url": pdf.replace("http://", "https://") if pdf else None,
            })
        return papers

    @staticmethod
    def _envelope(paper: dict[str, Any], fetched_at: str) -> RawEnvelope:
        return RawEnvelope(platform_item_id=paper.get("id"), url=paper.get("url"), title=paper.get("title"), payload={"paper": paper}, fetched_at=fetched_at)

    @staticmethod
    def _text(element: ET.Element, path: str, ns: dict[str, str]) -> str | None:
        found = element.find(path, ns)
        if found is None or found.text is None:
            return None
        return found.text.strip()
