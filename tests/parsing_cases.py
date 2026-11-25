"""Invented source envelopes; no publisher content or endpoints."""

import json

NS = "urn:synthetic:body"
DC = "http://purl.org/dc/elements/1.1/"


def item(body="<p>Synthetic evidence only.</p>", *, guid="synthetic-1", extra=""):
    return (
        f'<item><guid isPermaLink="false">{guid}</guid>'
        "<link>https://example.org/article</link><title>Synthetic title</title>"
        "<pubDate>supplied, not parsed</pubDate><author>synthetic byline</author>"
        '<source url="https://example.org/rss">synthetic publisher</source>'
        f"<s:body><![CDATA[{body}]]></s:body>{extra}</item>"
    )


def rss(items=None):
    content = item() if items is None else items
    return (
        f'<rss version="2.0" xmlns:s="{NS}" xmlns:dc="{DC}"><channel>'
        "<title>Synthetic channel</title><link>https://example.org/rss</link>"
        f"<description>Synthetic feed</description>{content}</channel></rss>"
    ).encode()


def catalog(entries=None, **context):
    return json.dumps(
        {
            "catalogTitle": "Synthetic catalog",
            **context,
            "entries": [{"id": "synthetic-1", "extension": {"keep": [None, True, "é"]}}]
            if entries is None
            else entries,
        },
        ensure_ascii=False,
    ).encode()
