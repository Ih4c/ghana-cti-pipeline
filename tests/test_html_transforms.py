"""Synthetic offline security, deterministic-output and exact-boundary regressions."""

import ast
import builtins
import io
import os
import random
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import FrozenInstanceError
from html.parser import HTMLParser
from pathlib import Path

import pytest

from ghana_cti_pipeline.collectors import (
    article_transforms,
    html_fragment,
    html_profile,
    html_sanitizer,
    text_extraction,
)
from ghana_cti_pipeline.collectors.article_transforms import transform_articles
from ghana_cti_pipeline.collectors.html_profile import (
    ALLOWED,
    ARTICLE_LIMIT,
    EXTRACTOR_VERSION,
    HTML_PARSER_PROFILE,
    SANITIZER_VERSION,
    TransformError,
)
from ghana_cti_pipeline.collectors.html_sanitizer import sanitize_html
from ghana_cti_pipeline.collectors.rss_parser import parse_rss
from ghana_cti_pipeline.collectors.text_extraction import extract_text
from ghana_cti_pipeline.core.digests import compute_digest


def fails(call, code=None):
    with pytest.raises(TransformError) as caught:
        call()
    if code:
        assert caught.value.code == code
    assert str(caught.value) == caught.value.code
    assert "CANARY" not in repr(caught.value)
    assert caught.value.__context__ is None or caught.value.__suppress_context__


GOLDEN = [
    ('<P class="x" onclick="bad()">A &amp; B</P>', "<p>A &amp; B</p>", "A & B"),
    (
        '<a href="https://example.org/trap">visible</a><span id="x"> text</span>',
        "visible text",
        "visible text",
    ),
    (
        "<div><h2>Heading</h2><p>First<br>Second</p></div>",
        "<div><h2>Heading</h2><p>First<br>Second</p></div>",
        "Heading\n\nFirst\nSecond",
    ),
    (
        "<ul><li>one</li><li><em>two</em></li></ul>",
        "<ul><li>one</li><li><em>two</em></li></ul>",
        "one\ntwo",
    ),
    (
        "<table><tr><th>A</th><th>B</th></tr><tr><td>C</td><td>D</td></tr></table>",
        "<table><tr><th>A</th><th>B</th></tr><tr><td>C</td><td>D</td></tr></table>",
        "A\tB\nC\tD",
    ),
    (
        "<pre><code>  a\r\n b\rc\n</code></pre>",
        "<pre><code>  a\r\n b\rc\n</code></pre>",
        "  a\n b\nc",
    ),
    (
        "<p>&lt;script&gt;inert&lt;/script&gt; &amp;lt;b&amp;gt;</p>",
        "<p>&lt;script&gt;inert&lt;/script&gt; &amp;lt;b&amp;gt;</p>",
        "<script>inert</script> &lt;b&gt;",
    ),
    ("<p>&copy; &#233; &#x1F600; e\u0301</p>", "<p>© é 😀 e\u0301</p>", "© é 😀 e\u0301"),
    (
        "<p>left</p><!--discard--><script>if (x < y) bad()</script><p>right</p>",
        "<p>left</p><p>right</p>",
        "left\n\nright",
    ),
    ("<p>A & B > C</p>", "<p>A &amp; B &gt; C</p>", "A & B > C"),
]


@pytest.mark.parametrize("original,sanitized,plain", GOLDEN)
def test_fixed_golden_vectors(original, sanitized, plain):
    assert sanitize_html(original) == sanitized
    assert extract_text(sanitized) == plain
    assert sanitize_html(sanitized) == sanitized
    result = transform_articles((original,))[0]
    assert result.original == original
    assert result.sanitized_html == sanitized
    assert result.plain_text == plain
    assert result.sanitizer_version == SANITIZER_VERSION
    assert result.extractor_version == EXTRACTOR_VERSION
    assert result.parser_profile == HTML_PARSER_PROFILE
    assert result == transform_articles((original,))[0]
    assert original not in repr(result)
    with pytest.raises(FrozenInstanceError):
        result.original = "changed"


@pytest.mark.parametrize(
    "tag",
    [
        "script",
        "style",
        "iframe",
        "object",
        "form",
        "button",
        "select",
        "textarea",
        "video",
        "audio",
        "picture",
        "svg",
        "math",
        "template",
        "noscript",
        "noembed",
        "xmp",
        "title",
        "unknown-element",
    ],
)
def test_drop_whole_unapproved_subtrees(tag):
    original = f"<p>safe</p><{tag}>CANARY</{tag}><p>end</p>"
    assert sanitize_html(original) == "<p>safe</p><p>end</p>"


@pytest.mark.parametrize(
    "tag",
    [
        "img",
        "embed",
        "input",
        "link",
        "meta",
        "base",
        "source",
        "track",
        "area",
        "col",
        "hr",
        "param",
        "wbr",
    ],
)
def test_drop_void_resources(tag):
    assert sanitize_html(f'<p>safe</p><{tag} src="https://example.org/trap" />') == "<p>safe</p>"


@pytest.mark.parametrize(
    "attributes",
    [
        'href="javascript:bad()"',
        'style="background:url(https://example.org/trap)"',
        'onclick="bad()"',
        'srcdoc="&lt;script&gt;bad()&lt;/script&gt;"',
        'xmlns="http://www.w3.org/2000/svg"',
        'id="clobber" name="clobber"',
        'data-trap="CANARY"',
        'is="custom-element"',
        "hidden disabled",
        "src=https://example.org/trap",
    ],
)
def test_no_attribute_survives(attributes):
    assert sanitize_html(f"<p {attributes}>safe</p>") == "<p>safe</p>"


@pytest.mark.parametrize(
    "raw",
    [
        "<plaintext>CANARY</plaintext>",
        "<p>unclosed",
        "</p>",
        "<p><strong>x</p></strong>",
        "<p/>",
        "<span/>",
        '<p title="unclosed>CANARY</p>',
        "<p =bad>CANARY</p>",
        '<p a="x"b="y">x</p>',
        '<p a="1" A="2">x</p>',
        "<p x=`bad`>x</p>",
        "<p/x>x</p>",
        "<p>less < text</p>",
        "<!-- unclosed",
        "<!-- invalid -- comment -->x",
        "<!-- x-- >x",
        "<!DOCTYPE html><p>x</p>",
        '<?xml version="1.0"?><p>x</p>',
        "<![CDATA[CANARY]]>",
        "<script>unclosed CANARY",
        '<p>ok</p><img src="CANARY"',
        "<svg><g/onload=bad()//<p>CANARY</p>",
        "<math><mtext><table><mglyph><style><!--</style><img src=x onerror=bad()>",
        '<noscript><p title="</noscript><img src=x onerror=bad()>">CANARY</p>',
        "<p><br></br></p>",
        "<p>x</p bogus>",
    ],
)
def test_malformed_and_mutation_payloads_fail_closed(raw):
    fails(lambda: sanitize_html(raw))


@pytest.mark.parametrize(
    "reference",
    [
        "&bogus;",
        "&amp",
        "&#0;",
        "&#xD800;",
        "&#x110000;",
        "&#999999999;",
        "&#x80;",
        "&#13",
        "&notit;",
    ],
)
def test_bad_references_fail(reference):
    fails(lambda: sanitize_html("<p>" + reference + "</p>"))


@pytest.mark.parametrize("attribute", ['x="&bogus;"', 'x="&amp"', 'x="&#0;"'])
def test_discarded_attributes_still_validate_references(attribute):
    fails(lambda: sanitize_html(f"<p {attribute}>safe</p>"))


@pytest.mark.parametrize("value", ["\x00", "\x01", "\x7f", "\x85", "\ud800"])
def test_invalid_characters(value):
    fails(lambda: sanitize_html("<p>" + value + "</p>"), "invalid_character")
    fails(lambda: extract_text(value), "invalid_character")


@pytest.mark.parametrize("fn", [sanitize_html, extract_text])
@pytest.mark.parametrize("value", [None, b"text", "", " \t\n"])
def test_strict_inputs(fn, value):
    fails(lambda: fn(value), "invalid_input")


@pytest.mark.parametrize(
    "raw",
    [
        '<p x="x">text</p>',
        "<P>x</P>",
        "<span>x</span>",
        "<br/>text",
        "<!--x-->text",
        "<p>&copy;</p>",
        "<p>&#65;</p>",
        "<script>x</script>",
        "A & B",
        "x > y",
    ],
)
def test_extractor_rejects_unsanitized_markup(raw):
    fails(lambda: extract_text(raw), "not_sanitized")


@pytest.mark.parametrize(
    "raw", ["<script>CANARY</script>", '<img src="https://example.org/trap">', "<!-- CANARY -->"]
)
def test_empty_sanitized_result_is_failure(raw):
    fails(lambda: sanitize_html(raw), "empty_output")


def test_empty_plain_result_and_empty_valid_batch():
    fails(lambda: extract_text("<p><br></p>"), "empty_output")
    fails(lambda: transform_articles(("<p></p>",)), "empty_output")
    assert transform_articles(()) == ()


@pytest.mark.parametrize("character", ["x", "é", "😀"])
def test_exact_input_and_output_byte_limits(character):
    raw = character * (ARTICLE_LIMIT // len(character.encode()))
    assert sanitize_html(raw) == raw
    assert extract_text(raw) == raw
    fails(lambda: sanitize_html(raw + "x"), "input_limit")
    fails(lambda: extract_text(raw + "x"), "input_limit")


def test_escaping_expansion_exact_output_limit():
    raw = ">" * (ARTICLE_LIMIT // 4)
    assert len(sanitize_html(raw).encode()) == ARTICLE_LIMIT
    fails(lambda: sanitize_html(raw + "x"), "output_limit")


def test_depth_including_dropped_subtrees_and_void_elements():
    for tag in ("div", "unknown"):
        prefix, suffix = "<" + tag + ">", "</" + tag + ">"
        valid = "<p>safe</p>" + prefix * 64 + "x" + suffix * 64
        assert sanitize_html(valid)
        fails(
            lambda tag=tag: sanitize_html(
                "<p>safe</p>" + ("<" + tag + ">") * 65 + "x" + ("</" + tag + ">") * 65
            ),
            "depth_limit",
        )
    fails(lambda: sanitize_html("<div>" * 64 + "<br>" + "</div>" * 64), "depth_limit")
    assert extract_text("<div>" * 64 + "x" + "</div>" * 64) == "x"


def test_node_budget_exact_and_shared_batch():
    raw = "<br>" * 49999 + "x"
    assert sanitize_html(raw) == raw
    assert extract_text(raw) == "x"
    fails(lambda: sanitize_html("<br>" + raw), "node_limit")
    half = "<br>" * 24999 + "x"
    assert len(transform_articles((half, half))) == 2
    fails(lambda: transform_articles((half, half, "x")), "node_limit")


def test_attribute_count_and_value_limits():
    attributes = " ".join(f'a{i}="x"' for i in range(32))
    assert sanitize_html(f"<p {attributes}>x</p>") == "<p>x</p>"
    fails(lambda: sanitize_html(f'<p {attributes} extra="x">x</p>'), "attribute_limit")
    assert sanitize_html('<p attr="' + "é" * 4096 + '">x</p>') == "<p>x</p>"
    fails(lambda: sanitize_html('<p attr="' + "é" * 4097 + '">x</p>'), "attribute_limit")


def test_batch_original_and_sanitized_aggregate_limits():
    field = "x" * ARTICLE_LIMIT
    assert len(transform_articles((field,) * 6)) == 6
    fails(lambda: transform_articles((field,) * 6 + ("x",)), "batch_limit")
    expanded = ">" * (ARTICLE_LIMIT // 4)
    assert len(transform_articles((expanded,) * 6)) == 6
    fails(lambda: transform_articles((expanded,) * 6 + ("x",)), "batch_limit")


def test_batch_type_count_versions_and_atomicity():
    fails(lambda: transform_articles(["x"]), "invalid_input")
    assert len(transform_articles(("x",) * 500)) == 500
    fails(lambda: transform_articles(("x",) * 501), "item_limit")
    fails(lambda: transform_articles(("safe", "<p>CANARY")), "malformed_html")
    assert transform_articles(("safe",))[0].plain_text == "safe"
    for version in ("future", 1, None):
        fails(lambda version=version: sanitize_html("x", version=version), "unsupported_version")
        fails(lambda version=version: extract_text("x", version=version), "unsupported_version")
        fails(
            lambda version=version: transform_articles(("x",), sanitizer_version=version),
            "unsupported_version",
        )
        fails(
            lambda version=version: transform_articles(("x",), extractor_version=version),
            "unsupported_version",
        )


def test_m106a_fields_and_existing_digests_compatible():
    raw = (
        b'<rss version="2.0"><channel><title>synthetic</title>'
        b"<link>https://example.org</link><description>synthetic</description>"
        b"<item><description>&lt;p&gt;A &amp;amp; B&lt;/p&gt;</description>"
        b"</item></channel></rss>"
    )
    original = parse_rss(raw, body_namespace="", body_local_name="description").items[0].body.value
    result = transform_articles((original,))[0]
    assert original == "<p>A &amp; B</p>" and result.plain_text == "A & B"
    for domain, value in (
        ("feed-field-html-utf8-v1", result.original),
        ("sanitized-html-utf8-v1", result.sanitized_html),
        ("plain-text-utf8-v1", result.plain_text),
    ):
        assert compute_digest(domain, value).domain == domain


class InertCheck(HTMLParser):
    def handle_starttag(self, tag, attrs):
        assert tag in ALLOWED and not attrs

    def handle_comment(self, data):
        raise AssertionError("Comments must not survive")

    def handle_decl(self, data):
        raise AssertionError("Declarations must not survive")

    def handle_pi(self, data):
        raise AssertionError("Instructions must not survive")


def test_generated_adversarial_fragments_are_rejected_or_inert():
    generator = random.Random(40602)
    tokens = [
        "<p>",
        "</p>",
        "<script>",
        "</script>",
        "<img src=x onerror=bad()>",
        "<svg>",
        "</svg>",
        "<!--x-->",
        "&lt;",
        "&amp;",
        "&#0;",
        "<",
        ">",
        "plain",
        "<span>",
        "</span>",
    ]
    for _ in range(500):
        value = "".join(generator.choices(tokens, k=12))
        try:
            output = sanitize_html(value)
        except TransformError:
            continue
        checker = InertCheck(convert_charrefs=False)
        checker.feed(output)
        checker.close()
        assert sanitize_html(output) == output


def test_no_side_effects_or_payload_logging(monkeypatch, capsys):
    attempts = []

    def denied(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("forbidden side effect")

    with monkeypatch.context() as patch:
        for module, names in (
            (builtins, ["open"]),
            (io, ["open"]),
            (os, ["open", "urandom"]),
            (Path, ["open", "read_text", "read_bytes", "write_text", "write_bytes"]),
            (socket, ["socket", "getaddrinfo", "gethostbyname", "create_connection"]),
            (time, ["time", "monotonic", "sleep", "perf_counter"]),
            (random, ["random", "randint", "getrandbits"]),
            (uuid, ["uuid4"]),
        ):
            for name in names:
                patch.setattr(module, name, denied)
        result = transform_articles(('<p>CANARY</p><img src="https://example.org/trap">',))[0]
        assert result.plain_text == "CANARY"
        assert "CANARY" not in repr(result)
        fails(lambda: sanitize_html("<p>CANARY"), "malformed_html")
    assert attempts == []
    assert capsys.readouterr() == ("", "")


def test_static_transform_boundaries():
    allowed = {
        "dataclasses",
        "io",
        "re",
        "html",
        "html.entities",
        "html.parser",
        "ghana_cti_pipeline.collectors.html_profile",
        "ghana_cti_pipeline.collectors.html_fragment",
        "ghana_cti_pipeline.collectors.html_sanitizer",
        "ghana_cti_pipeline.collectors.text_extraction",
    }
    for module in (
        article_transforms,
        html_profile,
        html_fragment,
        html_sanitizer,
        text_extraction,
    ):
        for node in ast.walk(ast.parse(Path(module.__file__).read_text())):
            if isinstance(node, ast.Import):
                assert {x.name for x in node.names} <= allowed
            elif isinstance(node, ast.ImportFrom):
                assert node.module in allowed and not node.level


def test_empty_table_cells_keep_column_separators():
    sanitized = "<table><tr><td></td><td>B</td><td></td></tr></table>"
    assert extract_text(sanitized) == "\tB\t"


def test_long_entity_and_chunk_runs_do_not_consume_extra_nodes():
    raw = "&amp;" * 50001
    assert sanitize_html(raw) == raw
    assert extract_text(raw) == "&" * 50001


def test_dropped_ancestor_never_releases_nested_allowed_markup():
    raw = "<p>safe</p><svg><foreignObject><div><p>CANARY</p></div></foreignObject></svg>"
    assert sanitize_html(raw) == "<p>safe</p>"
    raw = "<p>safe</p><form><p>CANARY</p><form><p>CANARY</p></form></form>"
    assert sanitize_html(raw) == "<p>safe</p>"


def test_html_reference_boundaries_and_nested_encoding():
    assert (
        extract_text(sanitize_html("&amp;#x3c; &amp;amp; &#x10FFFF;")) == "&#x3c; &amp; \U0010ffff"
    )
    assert sanitize_html('<p title="&amp; &quot;">x</p>') == "<p>x</p>"


def test_original_not_replaced_when_transform_changes_content():
    original = "<p>e\u0301</p><script>CANARY</script>"
    result = transform_articles((original,))[0]
    assert result.original == original and "CANARY" in result.original
    assert result.plain_text == "e\u0301" and result.plain_text != "é"
    with pytest.raises(ValueError, match="unsupported transformation error code"):
        TransformError("CANARY")


@pytest.mark.parametrize("attrs", [[("a", "x")] * 33, [("a", "x" * 4097)]])
def test_attribute_limits_precede_fragment_scan(monkeypatch, attrs):
    def denied(*args):
        raise AssertionError("Oversized attributes must reject before scanning")

    monkeypatch.setattr(html_fragment, "_TAG", type("NoScan", (), {"match": denied})())
    parser = html_fragment.FragmentParser("", html_profile.NodeBudget())
    fails(lambda: parser.start("p", attrs, closed=False), "attribute_limit")


@pytest.mark.parametrize(
    "shape,size,expected",
    [
        ("many_attributes", ARTICLE_LIMIT // 2, "attribute_limit"),
        ("many_attributes", ARTICLE_LIMIT, "attribute_limit"),
        ("long_value", ARTICLE_LIMIT, "attribute_limit"),
        ("long_name", ARTICLE_LIMIT, "success"),
        ("whitespace", ARTICLE_LIMIT, "success"),
        ("unfinished_value", ARTICLE_LIMIT, "malformed_html"),
    ],
)
def test_large_tag_shapes_finish_within_bounded_subprocess(shape, size, expected):
    prefix, suffix = "<p ", ">x</p>"
    room = size - len(prefix) - len(suffix)
    if shape == "many_attributes":
        middle = "a=x " * (room // 4) + " " * (room % 4)
    elif shape == "long_value":
        middle = 'a="' + "x" * (room - 4) + '"'
    elif shape == "long_name":
        middle = "a" * room
    elif shape == "whitespace":
        middle = " " * room
    else:
        middle = 'a="' + "x" * (room - 3)
    raw = prefix + middle + suffix
    assert len(raw.encode("utf-8")) == size <= ARTICLE_LIMIT
    # Kill a quadratic regression instead of leaving CI stuck in the parser.
    # This generous deadline includes interpreter/import/pipe overhead; it is not
    # a production timeout or a tight, machine-dependent microbenchmark.
    script = """
import sys
from ghana_cti_pipeline.collectors.html_profile import TransformError
from ghana_cti_pipeline.collectors.html_sanitizer import sanitize_html
try:
    result = sanitize_html(sys.stdin.read())
except TransformError as error:
    print(error.code)
else:
    print("success" if result == "<p>x</p>" else "unexpected_output")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        input=raw,
        text=True,
        capture_output=True,
        timeout=8,
        check=True,
    )
    assert completed.stdout.strip() == expected
    assert completed.stderr == ""
