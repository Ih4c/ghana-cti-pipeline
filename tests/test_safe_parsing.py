"""Offline adversarial and exact-limit coverage for pure source parsing."""

import ast
import builtins
import io
import json
import os
import random
import socket
import time
import uuid
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest
from parsing_cases import DC, NS, catalog, item, rss

from ghana_cti_pipeline.collectors import catalog_parser, parsing_values, rss_parser
from ghana_cti_pipeline.collectors.catalog_parser import parse_catalog
from ghana_cti_pipeline.collectors.parsing_values import (
    ARTICLE_BYTES,
    CATALOG_BYTES,
    PARSER_VERSION,
    RSS_BYTES,
    ParseError,
)
from ghana_cti_pipeline.collectors.rss_parser import parse_rss
from ghana_cti_pipeline.core.digests import canonical_json, compute_digest


def xml(raw, **kwargs):
    return parse_rss(raw, body_namespace=NS, body_local_name="body", **kwargs)


def js(raw):
    return parse_catalog(raw, entries_field="entries", native_id_field="id")


def failure(call, code):
    with pytest.raises(ParseError) as caught:
        call()
    assert caught.value.code == code
    assert str(caught.value) == code
    assert caught.value.__suppress_context__ or caught.value.__context__ is None


def test_fields_original_bytes_and_metadata_are_distinct():
    raw = rss(item(extra="<dc:creator>creator</dc:creator><dc:publisher>publisher</dc:publisher>"))
    result = xml(raw)
    assert result.parser_version == PARSER_VERSION
    parsed = result.items[0]
    fields = {(f.namespace, f.local_name): f for f in parsed.fields}
    assert fields["", "pubDate"].value == "supplied, not parsed"
    assert fields["", "source"].attributes == (("url", "https://example.org/rss"),)
    assert fields[DC, "creator"].value == "creator"
    assert fields[DC, "publisher"].value == "publisher"
    assert parsed.body.value == "<p>Synthetic evidence only.</p>"
    assert parsed.body.namespace == NS
    assert parsed.index == 0
    assert raw != parsed.body.value.encode()
    assert "Synthetic evidence" not in repr(result)
    with pytest.raises(FrozenInstanceError):
        parsed.index = 2


def test_entities_cdata_line_endings_and_unicode_are_decoded_once():
    raw = rss(item()).replace(
        b"<![CDATA[<p>Synthetic evidence only.</p>]]>",
        b"&lt;p&gt;&amp;amp;&#233;&#x1F600;\r\nx\ry<![CDATA[&literal;]]>&lt;/p&gt;",
    )
    assert xml(raw).items[0].body.value == "<p>&amp;é😀\nx\ny&literal;</p>"


@pytest.mark.parametrize(
    "prefix",
    [
        b"",
        b"\xef\xbb\xbf",
        b'<?xml version="1.0"?>',
        b'<?xml version="1.0" encoding="UTF-8"?>',
        b'<?xml version="1.0" encoding="utf-8"?>',
    ],
)
def test_utf8_xml(prefix):
    assert len(xml(prefix + rss()).items) == 1


@pytest.mark.parametrize(
    "declaration",
    [
        b'<?xml version="1.0" encoding="UTF-16"?>',
        b'<?xml version="1.0" encoding="ISO-8859-1"?>',
        b'<?xml version="1.1"?>',
    ],
)
def test_xml_declaration_rejects_conflicting_encodings(declaration):
    failure(lambda: xml(declaration + rss()), "encoding")


@pytest.mark.parametrize(
    "raw", [rss().decode().encode("utf-16"), rss() + b"\xff", b"\xef\xbb\xbf\xff"]
)
def test_xml_non_utf8(raw):
    failure(lambda: xml(raw), "encoding")


@pytest.mark.parametrize(
    "prefix",
    [
        b"<!DOCTYPE rss>",
        b'<!DOCTYPE rss SYSTEM "https://example.org/evil">',
        b'<!DOCTYPE rss [<!ENTITY x "boom">]>',
        b'<!DOCTYPE rss [<!ENTITY % x SYSTEM "file:///synthetic">%x;]>',
        b'<!DOCTYPE rss [<!ENTITY x "xxxxxxxx"><!ENTITY y "&x;&x;&x;&x;">]>',
        b'<?xml-stylesheet href="https://example.org/evil"?>',
    ],
)
def test_dtd_entities_and_processing_instructions_rejected(prefix):
    failure(lambda: xml(prefix + rss()), "unsafe_xml")


@pytest.mark.parametrize(
    "extra",
    [
        '<xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="file:///synthetic"/>',
        "<?unsafe instruction?>",
    ],
)
def test_external_resource_instructions_rejected(extra):
    failure(lambda: xml(rss(item(extra=extra))), "unsafe_xml")


@pytest.mark.parametrize(
    "raw",
    [
        rss()
        .replace(b"<p>Synthetic evidence only.</p>", b"&custom;")
        .replace(b"<![CDATA[", b"")
        .replace(b"]]>", b""),
        rss()[:-1],
        rss() + b"garbage",
        rss() + rss(),
        rss().replace(b"<title>", b'<title a="1" a="2">', 1),
        rss().replace(b"s:body", b"unbound:body"),
        rss().replace(b"Synthetic title", b"&#0;"),
    ],
)
def test_malformed_xml_fails_whole_batch(raw):
    failure(lambda: xml(raw), "invalid_xml")


@pytest.mark.parametrize(
    "raw",
    [
        b" ",
        b"<rss/>",
        b'<rss version="1.0"/>',
        b'<rss version="2.0"/>',
        b'<rss version="2.0"><channel/></rss>',
        rss("").replace(b"<title>Synthetic channel</title>", b""),
        rss("").replace(b"</channel>", b"</channel><channel/>"),
        rss("").replace(b"<channel>", b"<channel>unexpected text"),
        rss("").replace(b"</channel>", b"</channel><item/>"),
    ],
)
def test_invalid_envelopes(raw):
    with pytest.raises(ParseError):
        xml(raw)


def test_empty_valid_feed_not_retraction_and_no_required_item_metadata_invented():
    assert xml(rss("")).items == ()
    parsed = xml(rss("<item><s:body>only supplied content</s:body></item>")).items[0]
    assert parsed.fields == ()
    assert not hasattr(parsed, "publication_date")
    assert not hasattr(parsed, "retracted")


@pytest.mark.parametrize("body", ["", " \n\t", "\u2003"])
def test_empty_required_body(body):
    failure(lambda: xml(rss(item(body))), "required_body")


@pytest.mark.parametrize(
    "replacement",
    [
        b"",
        b"<s:body><p>nested XML</p></s:body>",
        b"<different:body xmlns:different='urn:wrong'>other</different:body>",
    ],
)
def test_missing_wrong_namespace_or_nested_body_has_no_fallback(replacement):
    raw = rss(item()).replace(
        b"<s:body><![CDATA[<p>Synthetic evidence only.</p>]]></s:body>", replacement
    )
    failure(lambda: xml(raw), "required_body")


def test_caller_selected_description_and_prefix_independence():
    raw = rss(item()).replace(b"s:body", b"description")
    assert (
        parse_rss(raw, body_namespace="", body_local_name="description")
        .items[0]
        .body.value.startswith("<p>")
    )
    renamed = rss().replace(b"xmlns:s=", b"xmlns:other=").replace(b"s:body", b"other:body")
    assert xml(renamed) == xml(rss())


@pytest.mark.parametrize(
    "extra", ["<title>duplicate</title>", "<s:body>duplicate</s:body>", "<guid>duplicate</guid>"]
)
def test_duplicate_fields_fail(extra):
    failure(lambda: xml(rss(item(extra=extra))), "duplicate_field")


def test_duplicate_native_ids_compare_full_item_including_extensions():
    assert len(xml(rss(item() + item())).items) == 2
    for changed in (
        item("changed"),
        item(extra="<extension>changed</extension>"),
        item().replace("Synthetic title", "changed"),
    ):
        failure(lambda changed=changed: xml(rss(item() + changed)), "conflicting_id")
    assert len(xml(rss(item() + item(guid="another"))).items) == 2
    # Entity/CDATA spelling alone does not conflict; parsed infoset is compared.
    one = item("a&b")
    two = one.replace("<![CDATA[a&b]]>", "a&amp;b")
    assert len(xml(rss(one + two)).items) == 2


@pytest.mark.parametrize("character", ["x", "é", "😀"])
def test_article_exact_utf8_byte_limit_and_one_byte_over(character):
    body = character * (ARTICLE_BYTES // len(character.encode()))
    assert xml(rss(item(body))).items[0].body.value == body
    failure(lambda: xml(rss(item(body + "x"))), "field_limit")


@pytest.mark.parametrize(
    "name,limit",
    [
        ("title", 512),
        ("link", 4096),
        ("author", 256),
        ("source", 256),
        ("pubDate", 8192),
        ("dc:creator", 256),
        ("dc:publisher", 256),
        ("description", 65536),
    ],
)
def test_rss_metadata_character_limits(name, limit):
    base = "<item><s:body>full</s:body><{0}>{1}</{0}></item>"
    value = "é" * limit
    assert xml(rss(base.format(name, value))).items[0].fields[0].value == value
    failure(lambda: xml(rss(base.format(name, value + "x"))), "field_limit")


@pytest.mark.parametrize("url", [False, True])
def test_guid_boundaries(url):
    prefix, limit = ("https://example.org/", 4096) if url else ("id-", 256)
    value = prefix + "a" * (limit - len(prefix))
    assert xml(rss(item(guid=value))).items[0].fields[0].value == value
    failure(lambda: xml(rss(item(guid=value + "x"))), "field_limit")


def test_xml_depth_includes_unknown_elements():
    extra = "<x>" * 61 + "v" + "</x>" * 61
    assert xml(rss(item(extra=extra)))
    failure(lambda: xml(rss(item(extra="<x>" + extra + "</x>"))), "depth_limit")


@pytest.mark.parametrize("count", [500, 501])
def test_feed_item_count(count):
    raw = rss("".join(item(guid=f"i-{i}") for i in range(count)))
    if count == 500:
        assert len(xml(raw).items) == count
    else:
        failure(lambda: xml(raw), "item_limit")


@pytest.mark.parametrize(
    "parse,raw,limit", [(xml, rss(), RSS_BYTES), (js, catalog(), CATALOG_BYTES)]
)
def test_exact_response_limits(parse, raw, limit):
    exact = raw + b" " * (limit - len(raw))
    assert parse(exact)
    failure(lambda: parse(exact + b" "), "input_limit")


@pytest.mark.parametrize("parse", [xml, js])
@pytest.mark.parametrize("raw", [b"", "text", None, bytearray(b"test")])
def test_strict_input_types(parse, raw):
    failure(lambda: parse(raw), "invalid_input")


def test_complete_catalog_with_extensions_and_exact_decimal_values():
    raw = (
        b'{"entries":[{"id":"one","future":{"x":1.234567890123456789,'
        b'"y":1e-9999,"z":-0.0},"date":"invalid-as-supplied"}],'
        b'"unknown":[true,null,"e\\u0301"]}'
    )
    result = js(raw)
    assert result.document["unknown"] == [True, None, "e\u0301"]
    assert result.entries[0]["future"]["x"] == Decimal("1.234567890123456789")
    assert result.entries[0]["future"]["y"] != 0
    assert result.entries[0]["future"]["z"].is_signed()
    assert result.entries[0]["date"] == "invalid-as-supplied"
    assert "future" not in repr(result)
    assert result.parser_version == PARSER_VERSION
    with pytest.raises(ValueError, match="unsupported canonical JSON value"):
        canonical_json(result.entries[0])


def test_standard_catalog_compatible_with_existing_digest_profile():
    parsed = js(catalog()).entries[0]
    assert parsed == json.loads(catalog())["entries"][0]
    assert compute_digest("catalog-entry-json-v1", parsed) == compute_digest(
        "catalog-entry-json-v1", json.loads(catalog())["entries"][0]
    )
    assert js(b"\xef\xbb\xbf" + catalog()) == js(catalog())


@pytest.mark.parametrize(
    "raw",
    [
        b'{"entries":[],"entries":[]}',
        b'{"entries":[{"id":"one","extra":{"x":1,"x":2}}]}',
        b'{"entries":[{"id":"one","\\u0069d":"two"}]}',
    ],
)
def test_duplicate_json_keys_at_every_level(raw):
    failure(lambda: js(raw), "duplicate_field")


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "undefined", "+1", "01", "1."])
def test_invalid_json_numbers(token):
    raw = ('{"entries":[{"id":"one","value":' + token + "}]}").encode()
    failure(lambda: js(raw), "invalid_json")


@pytest.mark.parametrize(
    "raw",
    [
        b" ",
        b"{}",
        b"[]",
        b"null",
        catalog([]),
        catalog([{}]),
        catalog([1]),
        catalog([{"id": None}]),
        catalog([{"id": " "}]),
        b'{"entries":{}}',
    ],
)
def test_invalid_json_envelopes(raw):
    with pytest.raises(ParseError):
        js(raw)


@pytest.mark.parametrize(
    "raw", [catalog()[:-1], catalog() + b"x", b'{"entries":[{"id":"one","x":"unescaped\n"}]}']
)
def test_malformed_json_no_partial_results(raw):
    failure(lambda: js(raw), "invalid_json")


@pytest.mark.parametrize(
    "raw",
    [
        catalog() + b"\xff",
        catalog().decode().encode("utf-16"),
        b'{"entries":[{"id":"one","x":"\\ud800"}]}',
        b'{"entries":[{"id":"one","\\udfff":1}]}',
    ],
)
def test_json_unicode_rejections(raw):
    failure(lambda: js(raw), "encoding")


def test_json_depth_preflight_handles_quoted_brackets():
    raw = b'{"entries":[{"id":"one","x":' + b"[" * 61 + b'"[\\"{]"' + b"]" * 61 + b"}]}"
    assert js(raw)
    failure(lambda: js(raw.replace(b'"x":', b'"x":[')[:-3] + b"]}]}"), "depth_limit")
    failure(lambda: js(b"[" * 100000), "depth_limit")


@pytest.mark.parametrize("count", [10000, 10001])
def test_catalog_entry_count(count):
    raw = catalog([{"id": str(i)} for i in range(count)])
    if count == 10000:
        assert len(js(raw).entries) == count
    else:
        failure(lambda: js(raw), "item_limit")


@pytest.mark.parametrize("key", [False, True])
def test_json_metadata_exact_limits(key):
    entry = {"id": "one", ("x" * 8192 if key else "field"): (None if key else "é" * 8192)}
    assert js(catalog([entry]))
    entry = {"id": "one", ("x" * 8193 if key else "field"): (None if key else "é" * 8193)}
    failure(lambda: js(catalog([entry])), "field_limit")


def test_catalog_native_id_boundary():
    assert js(catalog([{"id": "i" * 256}]))
    failure(lambda: js(catalog([{"id": "i" * 257}])), "field_limit")


def test_catalog_duplicates_compare_all_fields_without_bool_integer_aliasing():
    first = {"id": "one", "extension": {"x": [True, None]}}
    reordered = {"extension": {"x": [True, None]}, "id": "one"}
    assert len(js(catalog([first, reordered])).entries) == 2
    for changed in (
        {"id": "one", "extension": {"x": [1, None]}},
        {"id": "one"},
        {"id": "one", "extension": {"x": [True]}},
    ):
        failure(lambda changed=changed: js(catalog([first, changed])), "conflicting_id")


def test_deterministic_integer_safety_limit():
    prefix = b'{"entries":[{"id":"one","value":'
    assert js(prefix + b"9" * 4300 + b"}]}")
    failure(lambda: js(prefix + b"9" * 4301 + b"}]}"), "invalid_json")


@pytest.mark.parametrize(
    "namespace,local",
    [(None, "body"), ("", ""), ("", "title"), ("", "a:b"), ("a|b", "body"), ("", "a" * 257)],
)
def test_invalid_rss_configuration(namespace, local):
    failure(
        lambda: parse_rss(rss(), body_namespace=namespace, body_local_name=local), "configuration"
    )


@pytest.mark.parametrize("entries,native", [(None, "id"), ("entries", ""), ("x" * 257, "id")])
def test_invalid_catalog_configuration(entries, native):
    failure(
        lambda: parse_catalog(catalog(), entries_field=entries, native_id_field=native),
        "configuration",
    )


def test_safe_errors_exclude_payload(capsys):
    failure(lambda: js(b'{"SECRET_CANARY": '), "invalid_json")
    failure(lambda: xml(b"<SECRET_CANARY>"), "envelope")
    assert capsys.readouterr() == ("", "")
    with pytest.raises(ValueError, match="unsupported parse error code"):
        ParseError("SECRET_CANARY")


def test_parsers_perform_no_io_time_or_randomness(monkeypatch):
    xml_input, json_input = rss(), catalog()
    attempts = []

    def denied(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("Forbidden side effect")

    with monkeypatch.context() as patch:
        for module, names in (
            (builtins, ["open"]),
            (io, ["open"]),
            (os, ["open", "urandom"]),
            (Path, ["open", "read_bytes", "read_text", "write_bytes", "write_text"]),
            (socket, ["socket", "getaddrinfo", "gethostbyname", "create_connection"]),
            (time, ["time", "monotonic", "perf_counter", "sleep"]),
            (random, ["random", "randint", "getrandbits"]),
            (uuid, ["uuid4"]),
        ):
            for name in names:
                patch.setattr(module, name, denied)
        assert xml(xml_input) == xml(xml_input)
        assert js(json_input) == js(json_input)
        failure(lambda: xml(b'<!DOCTYPE rss SYSTEM "file:///synthetic">' + xml_input), "unsafe_xml")
    assert attempts == []


def test_parser_imports_have_no_transport_storage_clock_or_randomness():
    allowed = {
        "dataclasses",
        "json",
        "decimal",
        "hashlib",
        "io",
        "xml.parsers",
        "ghana_cti_pipeline.collectors.parsing_values",
    }
    for module in (parsing_values, rss_parser, catalog_parser):
        tree = ast.parse(Path(module.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert {alias.name for alias in node.names} <= allowed
            elif isinstance(node, ast.ImportFrom):
                assert node.module in allowed and node.level == 0


def test_truncated_required_field_rejects_after_an_earlier_valid_item():
    raw = rss(item() + item(guid="two"))
    cutoff = raw.rindex(b"</s:body>")
    failure(lambda: xml(raw[:cutoff]), "invalid_xml")
    failure(lambda: xml(rss(item() + "<item><title>metadata only</title></item>")), "required_body")
    assert len(xml(rss(item())).items) == 1  # No poisoned module state after failure.


@pytest.mark.parametrize("attribute,limit", [("url", 4096), ("extension", 8192)])
def test_xml_attribute_exact_limits(attribute, limit):
    good = item(extra=f'<extension {attribute}="' + "é" * limit + '"/>')
    assert xml(rss(good))
    bad = item(extra=f'<extension {attribute}="' + "é" * (limit + 1) + '"/>')
    failure(lambda: xml(rss(bad)), "field_limit")


def test_optional_guid_behavior_and_invalid_attributes():
    for fragment in ("<guid/>", "<guid> </guid>", '<guid isPermaLink="maybe">one</guid>'):
        failure(
            lambda fragment=fragment: xml(
                rss("<item>" + fragment + "<s:body>full</s:body></item>")
            ),
            "envelope",
        )
    raw = rss(item()).replace(b' isPermaLink="false"', b"")
    assert xml(raw).items[0].fields[0].attributes == ()


def test_plain_html_is_neither_executed_nor_sanitized():
    body = '<script>untrusted()</script><img src="https://example.org/trap">'
    assert xml(rss(item(body))).items[0].body.value == body


def test_json_negative_zero_and_unicode_are_not_normalized():
    result = js(
        b'{"entries":[{"id":"one","decimal":-0.0,"text":"\\ud83d\\ude00","a":"e\\u0301","b":"\\u00e9"}]}'
    )
    entry = result.entries[0]
    assert entry["decimal"].is_signed()
    assert entry["text"] == "😀"
    assert entry["a"] != entry["b"]


def test_excess_catalog_count_fails_whole_batch_and_next_call_is_independent():
    failure(lambda: js(catalog([{"id": "ok"}, {"id": " "}])), "envelope")
    assert len(js(catalog()).entries) == 1
