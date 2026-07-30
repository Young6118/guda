from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class RawEnvelope:
    platform_item_id: str | None
    url: str | None
    title: str | None
    payload: dict[str, Any]
    fetched_at: str


@dataclass(frozen=True)
class EvidenceDraft:
    platform: str
    item_type: str
    url: str | None
    title: str | None
    text: str
    author_display: str | None = None
    created_at_source: str | None = None
    engagement: dict[str, Any] = field(default_factory=dict)
    parent_url: str | None = None
    language: str | None = None
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompanyDraft:
    provider: str
    company_name: str
    credit_code: str | None = None
    company_id_provider: str | None = None
    stock_code: str | None = None
    exchange: str | None = None
    registration_status: str | None = None
    legal_person: str | None = None
    industry: str | None = None
    region: str | None = None
    registration_info: dict[str, Any] = field(default_factory=dict)
    risk_snapshot: dict[str, Any] = field(default_factory=dict)
    market_profile: dict[str, Any] = field(default_factory=dict)
    geo_profile: dict[str, Any] = field(default_factory=dict)


class SourceConnector(Protocol):
    name: str
    platform: str
    acquisition_layer: str

    def test_connection(self) -> bool: ...

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]: ...

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]: ...
