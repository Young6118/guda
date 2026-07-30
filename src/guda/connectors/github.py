from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from guda.connectors.base import EvidenceDraft, RawEnvelope


class GitHubConnector:
    name = "github"
    platform = "github"
    acquisition_layer = "official_api"

    def __init__(self, *, client: httpx.Client | None = None, token: str | None = None, timeout_seconds: int = 30):
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "guda/0.1"}
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        auth_token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        self.client = client or httpx.Client(base_url="https://api.github.com", headers=headers, timeout=timeout_seconds)

    def test_connection(self) -> bool:
        response = self.client.get("/rate_limit")
        return response.status_code < 500

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        raw: list[RawEnvelope] = []
        repo = self._repo_from_query(query)
        repo_query = query.replace(f"repo:{repo}", "").strip() if repo else query

        for item in self._search_repositories(repo_query or query, max(1, min(limit, 5))):
            raw.append(self._envelope("repo", item, item.get("id"), item.get("html_url"), item.get("full_name"), fetched_at))
            if len(raw) >= limit:
                return raw

        issue_query = f"{repo_query or query} repo:{repo}" if repo else query
        for item in self._search_issues(issue_query, max(1, limit - len(raw))):
            raw.append(self._envelope("issue", item, item.get("id"), item.get("html_url"), item.get("title"), fetched_at))
            if len(raw) >= limit:
                return raw

        if repo and len(raw) < limit:
            for item in self._releases(repo, limit - len(raw)):
                raw.append(self._envelope("release", item, item.get("id"), item.get("html_url"), item.get("name") or item.get("tag_name"), fetched_at))
                if len(raw) >= limit:
                    return raw
        return raw

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        kind = raw.payload.get("kind")
        item = raw.payload.get("item", {})
        if kind == "repo":
            text = item.get("description") or raw.title or ""
            return [EvidenceDraft(platform="github", item_type="repo", url=raw.url, title=item.get("full_name"), text=text, created_at_source=item.get("created_at"), engagement={"stars": item.get("stargazers_count"), "forks": item.get("forks_count"), "open_issues": item.get("open_issues_count")})]
        if kind == "release":
            return [EvidenceDraft(platform="github", item_type="release", url=raw.url, title=raw.title, text=item.get("body") or raw.title or "", author_display=(item.get("author") or {}).get("login"), created_at_source=item.get("published_at"), engagement={})]
        repo_url = item.get("repository_url", "")
        return [EvidenceDraft(platform="github", item_type="issue", url=raw.url, title=item.get("title"), text=item.get("body") or item.get("title") or "", author_display=(item.get("user") or {}).get("login"), created_at_source=item.get("created_at"), engagement={"state": item.get("state"), "comments": item.get("comments"), "repository": repo_url.rsplit("/", 2)[-2:]})]

    def _search_repositories(self, query: str, limit: int) -> list[dict[str, Any]]:
        response = self.client.get("/search/repositories", params={"q": query, "per_page": limit, "sort": "updated"})
        response.raise_for_status()
        return list(response.json().get("items", []))

    def _search_issues(self, query: str, limit: int) -> list[dict[str, Any]]:
        q = query if "is:" in query else f"{query} is:issue"
        response = self.client.get("/search/issues", params={"q": q, "per_page": limit, "sort": "updated"})
        response.raise_for_status()
        return list(response.json().get("items", []))

    def _releases(self, repo: str, limit: int) -> list[dict[str, Any]]:
        response = self.client.get(f"/repos/{repo}/releases", params={"per_page": limit})
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    @staticmethod
    def _repo_from_query(query: str) -> str | None:
        for token in query.split():
            if token.startswith("repo:") and "/" in token:
                return token.split(":", 1)[1]
        return None

    @staticmethod
    def _envelope(kind: str, item: dict[str, Any], item_id: Any, url: str | None, title: str | None, fetched_at: str) -> RawEnvelope:
        return RawEnvelope(platform_item_id=f"{kind}:{item_id}", url=url, title=title, payload={"kind": kind, "item": item}, fetched_at=fetched_at)
