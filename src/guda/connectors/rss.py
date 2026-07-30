from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class RSSConnector:
    name = "rss"
    platform = "rss"
    acquisition_layer = "public_endpoint"

    def __init__(self, *, client: httpx.Client | None = None, timeout_seconds: int = 30):
        self.client = client or httpx.Client(timeout=timeout_seconds, headers={"User-Agent": "guda/0.1"}, follow_redirects=True)

    def test_connection(self) -> bool:
        return True

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        feed_url, filters = self._parse_query(query)
        response = self.client.get(feed_url)
        response.raise_for_status()
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        entries = self._filter_entries(self._parse(response.text, feed_url), filters)[:limit]
        return [RawEnvelope(platform_item_id=entry.get("id") or entry.get("url"), url=entry.get("url"), title=entry.get("title"), payload={"feed_url": feed_url, "entry": entry}, fetched_at=fetched_at) for entry in entries]

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        entry = raw.payload.get("entry", {})
        text = entry.get("summary") or entry.get("content") or raw.title or ""
        return [EvidenceDraft(platform="rss", item_type="article", url=raw.url, title=raw.title, text=text, author_display=entry.get("author"), created_at_source=entry.get("published_at"), engagement={"feed_url": raw.payload.get("feed_url")})]

    def _parse(self, xml_text: str, feed_url: str) -> list[dict[str, Any]]:
        root = ET.fromstring(xml_text)
        if root.tag.endswith("feed"):
            return self._parse_atom(root, feed_url)
        return self._parse_rss(root, feed_url)

    @staticmethod
    def _parse_query(query: str) -> tuple[str, list[str]]:
        tokens = query.strip().split()
        feed_url = None
        filters: list[str] = []
        for token in tokens:
            if token.startswith("feed:"):
                feed_url = token.split(":", 1)[1]
            elif token.startswith("http://") or token.startswith("https://"):
                feed_url = token
            elif token.startswith("keywords:"):
                filters.extend(part.strip().lower() for part in token.split(":", 1)[1].split(",") if part.strip())
            elif not token.startswith("q:"):
                filters.append(token.lower())
        if not feed_url:
            raise ValueError("rss query must include feed URL")
        return feed_url, filters

    @staticmethod
    def _filter_entries(entries: list[dict[str, Any]], filters: list[str]) -> list[dict[str, Any]]:
        if not filters:
            return entries
        filtered = []
        for entry in entries:
            haystack = " ".join(str(entry.get(key) or "") for key in ("title", "summary", "content")).lower()
            if any(term in haystack for term in filters):
                filtered.append(entry)
        return filtered

    def _parse_atom(self, root: ET.Element, feed_url: str) -> list[dict[str, Any]]:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = []
        for entry in root.findall("a:entry", ns):
            link = entry.find("a:link[@href]", ns)
            author = entry.find("a:author/a:name", ns)
            entries.append({
                "id": self._text(entry, "a:id", ns),
                "title": self._text(entry, "a:title", ns),
                "url": link.get("href") if link is not None else feed_url,
                "summary": self._text(entry, "a:summary", ns) or self._text(entry, "a:content", ns),
                "author": author.text if author is not None else None,
                "published_at": self._text(entry, "a:updated", ns) or self._text(entry, "a:published", ns),
            })
        return entries

    def _parse_rss(self, root: ET.Element, feed_url: str) -> list[dict[str, Any]]:
        entries = []
        for item in root.findall("./channel/item"):
            published = self._text(item, "pubDate")
            entries.append({
                "id": self._text(item, "guid") or self._text(item, "link"),
                "title": self._text(item, "title"),
                "url": self._text(item, "link") or feed_url,
                "summary": self._text(item, "description"),
                "author": self._text(item, "author"),
                "published_at": self._normalize_date(published),
            })
        return entries

    @staticmethod
    def _text(element: ET.Element, path: str, ns: dict[str, str] | None = None) -> str | None:
        found = element.find(path, ns or {})
        if found is None or found.text is None:
            return None
        return found.text.strip()

    @staticmethod
    def _normalize_date(value: str | None) -> str | None:
        if not value:
            return None
        try:
            return parsedate_to_datetime(value).isoformat()
        except (TypeError, ValueError):
            return value
