from __future__ import annotations

import httpx

from guda.connectors.arxiv import ArxivConnector


def test_arxiv_connector_normalizes_atom_entries() -> None:
    xml = """<?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns='http://www.w3.org/2005/Atom' xmlns:arxiv='http://arxiv.org/schemas/atom'>
      <entry>
        <id>http://arxiv.org/abs/2607.12345v1</id>
        <updated>2026-07-30T00:00:00Z</updated>
        <published>2026-07-29T00:00:00Z</published>
        <title>Agentic Data Systems</title>
        <summary>We study evidence-backed agents.</summary>
        <author><name>Alice Smith</name></author>
        <arxiv:primary_category term='cs.AI'/>
        <category term='cs.AI'/>
        <link href='http://arxiv.org/pdf/2607.12345v1' title='pdf'/>
      </entry>
    </feed>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=xml)

    connector = ArxivConnector(client=httpx.Client(transport=httpx.MockTransport(handler), base_url="https://export.arxiv.org"))

    raw = connector.fetch_raw("agentic data systems", 5)[0]
    evidence = connector.normalize(raw)[0]

    assert raw.platform_item_id == "2607.12345v1"
    assert evidence.platform == "arxiv"
    assert evidence.title == "Agentic Data Systems"
    assert evidence.engagement["primary_category"] == "cs.AI"
