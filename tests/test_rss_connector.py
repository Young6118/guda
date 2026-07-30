from __future__ import annotations

import httpx

from guda.connectors.rss import RSSConnector


def test_rss_connector_parses_atom_feed() -> None:
    feed = """<?xml version='1.0' encoding='utf-8'?>
    <feed xmlns='http://www.w3.org/2005/Atom'>
      <title>Example Feed</title>
      <entry>
        <id>tag:example.com,2026:1</id>
        <title>Agent tooling gets better</title>
        <link href='https://example.com/post'/>
        <updated>2026-07-30T00:00:00Z</updated>
        <summary>Developers want less manual deployment.</summary>
        <author><name>Alice</name></author>
      </entry>
    </feed>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=feed, headers={"content-type": "application/atom+xml"})

    connector = RSSConnector(client=httpx.Client(transport=httpx.MockTransport(handler)))

    raw_items = connector.fetch_raw("feed:https://example.com/feed.xml keywords:deployment", 5)
    evidence = connector.normalize(raw_items[0])

    assert len(raw_items) == 1
    assert evidence[0].title == "Agent tooling gets better"
    assert evidence[0].url == "https://example.com/post"
    assert "deployment" in evidence[0].text
