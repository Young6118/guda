from __future__ import annotations

from typing import Any

from guda.connectors.tianyan_ai import TianyanAIConnector


class FakeTianyanClient:
    def search_companies(self, query: str, head: int = 20) -> dict[str, Any]:
        return {
            "query": query,
            "items": [
                {
                    "name": "宁德时代新能源科技股份有限公司",
                    "creditCode": "91350900587527783P",
                    "regStatus": "存续",
                }
            ],
        }

    def registration_info(self, company_name: str, head: int = 80) -> dict[str, Any]:
        return {
            "name": company_name,
            "creditCode": "91350900587527783P",
            "regStatus": "存续",
            "legalPersonName": "曾毓群",
            "industry": "电气机械和器材制造业",
            "regLocation": "福建省宁德市",
        }


def test_tianyan_connector_normalizes_company_enrichment() -> None:
    connector = TianyanAIConnector(client=FakeTianyanClient())

    raw_items = connector.fetch_raw("宁德时代", 5)
    companies = [company for raw in raw_items for company in connector.normalize_companies(raw)]

    assert len(raw_items) == 1
    assert companies[0].company_name == "宁德时代新能源科技股份有限公司"
    assert companies[0].credit_code == "91350900587527783P"
    assert companies[0].registration_status == "存续"
    assert companies[0].legal_person == "曾毓群"


def test_tianyan_connector_reads_registration_sources_base_shape() -> None:
    connector = TianyanAIConnector(client=FakeTianyanClient())
    raw = connector.fetch_raw("宁德时代", 1)[0]
    raw = type(raw)(
        platform_item_id=raw.platform_item_id,
        url=raw.url,
        title=raw.title,
        fetched_at=raw.fetched_at,
        payload={
            "registration": {
                "sources": {
                    "base": {
                        "name": "宁德时代新能源科技股份有限公司",
                        "creditCode": "91350900587527783P",
                        "regStatus": "存续",
                        "legalPersonName": "曾毓群",
                        "industry": "电气机械和器材制造业",
                        "regLocation": "福建省宁德市蕉城区漳湾镇新港路2号",
                    }
                }
            }
        },
    )

    company = connector.normalize_companies(raw)[0]

    assert company.credit_code == "91350900587527783P"
    assert company.registration_status == "存续"
    assert company.legal_person == "曾毓群"
