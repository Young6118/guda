from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from guda.connectors.base import CompanyDraft, EvidenceDraft, RawEnvelope



class TianyanClientProtocol(Protocol):
    def search_companies(self, query: str, head: int = 20) -> dict[str, Any]: ...

    def registration_info(self, company_name: str, head: int = 80) -> dict[str, Any]: ...


class TianyanAIConnector:
    name = "tianyan_ai"
    platform = "tianyan_ai"
    acquisition_layer = "official_api"

    def __init__(self, *, client: TianyanClientProtocol | None = None):
        self.client = client

    def _get_client(self) -> TianyanClientProtocol:
        if self.client is None:
            from guda.integrations.tianyan_ai.client import TianyanAIClient

            self.client = TianyanAIClient()
        return self.client

    def test_connection(self) -> bool:
        self._get_client().search_companies("宁德时代", head=1)
        return True

    def fetch_raw(self, query: str, limit: int) -> list[RawEnvelope]:
        client = self._get_client()
        search = client.search_companies(query, head=limit)
        candidates = self._candidate_names(search)
        if not candidates:
            candidates = [query]
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        raw: list[RawEnvelope] = []
        for name in candidates[:limit]:
            registration = client.registration_info(name, head=80)
            company_name = self._first(registration, "name", "companyName", "company_name") or name
            raw.append(
                RawEnvelope(
                    platform_item_id=company_name,
                    url=None,
                    title=company_name,
                    payload={"query": query, "search": search, "registration": registration},
                    fetched_at=fetched_at,
                )
            )
        return raw

    def normalize(self, raw: RawEnvelope) -> list[EvidenceDraft]:
        company = self.normalize_companies(raw)[0]
        parts = [company.company_name]
        if company.registration_status:
            parts.append(f"registration status: {company.registration_status}")
        if company.industry:
            parts.append(f"industry: {company.industry}")
        if company.region:
            parts.append(f"region: {company.region}")
        return [
            EvidenceDraft(
                platform="tianyan_ai",
                item_type="company_enrichment",
                url=None,
                title=company.company_name,
                text="; ".join(parts),
                entities=[company.company_name],
            )
        ]

    def normalize_companies(self, raw: RawEnvelope) -> list[CompanyDraft]:
        data = raw.payload.get("registration", {})
        if isinstance(data.get("sources"), dict) and isinstance(data["sources"].get("base"), dict):
            data = data["sources"]["base"]
        company_name = self._first(data, "name", "companyName", "company_name") or raw.title or "unknown"
        return [
            CompanyDraft(
                provider="tianyan_ai",
                company_name=company_name,
                credit_code=self._first(data, "creditCode", "credit_code", "unifiedSocialCreditCode"),
                company_id_provider=self._first(data, "id", "companyId", "company_id"),
                registration_status=self._first(data, "regStatus", "registration_status", "status"),
                legal_person=self._first(data, "legalPersonName", "legal_person", "legalPerson"),
                industry=self._first(data, "industry", "industryName"),
                region=self._first(data, "regLocation", "region", "base"),
                registration_info=data,
            )
        ]

    @staticmethod
    def _candidate_names(search: dict[str, Any]) -> list[str]:
        for key in ("items", "result", "data", "companies"):
            value = search.get(key)
            if isinstance(value, list):
                names = []
                for item in value:
                    if isinstance(item, dict):
                        name = TianyanAIConnector._first(item, "name", "companyName", "company_name")
                        if name:
                            names.append(name)
                if names:
                    return names
        return []

    @staticmethod
    def _first(data: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = data.get(key)
            if value not in (None, ""):
                return str(value)
        return None
