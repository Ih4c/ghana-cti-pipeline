"""A strict fragment grammar around HTMLParser, never browser error recovery."""

import re
from html.entities import html5
from html.parser import HTMLParser

from ghana_cti_pipeline.collectors.html_profile import (
    ALLOWED,
    DEPTH_LIMIT,
    VOID,
    NodeBudget,
    TransformError,
    characters,
)

_TAG = re.compile(r"<[A-Za-z][A-Za-z0-9-]*")
_ATTR = re.compile(
    r"""([A-Za-z_:][A-Za-z0-9_.:-]*)(?:[\t\n\r ]*=[\t\n\r ]*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?"""
)
_END = re.compile(r"</([A-Za-z][A-Za-z0-9-]*)[\t\n\r ]*>")
_REF = re.compile(r"&(#(?:[xX][0-9a-fA-F]+|[0-9]+)|[A-Za-z][A-Za-z0-9]*);")


def reference(token: str) -> str:
    if token.startswith("#"):
        digits = token[2:] if token[1:2].lower() == "x" else token[1:]
        if len(digits) > 8:
            raise TransformError("invalid_reference")
        try:
            point = int(digits, 16 if token[1:2].lower() == "x" else 10)
            value = chr(point)
        except (ValueError, OverflowError):
            raise TransformError("invalid_reference") from None
        if 0xD800 <= point <= 0xDFFF or point == 0:
            raise TransformError("invalid_reference")
    else:
        value = html5.get(token + ";")
        if value is None:
            raise TransformError("invalid_reference")
    characters(value)
    return value


def attribute_references(raw: str):
    # Attributes are discarded, but do not silently accept malformed references.
    for match in re.finditer(r"&(?=[A-Za-z#])", raw):
        ref = _REF.match(raw, match.start())
        if ref is None:
            raise TransformError("invalid_reference")
        reference(ref.group(1))


class FragmentParser(HTMLParser):
    # Freeze lexical modes across Python 3.11/3.14; other containers are strict
    # balanced markup and are dropped, never rendered with browser semantics.
    CDATA_CONTENT_ELEMENTS = ("script", "style")
    RCDATA_CONTENT_ELEMENTS = ()

    def __init__(self, source: str, nodes: NodeBudget, *, canonical=False):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.cursor = 0
        self.stack: list[str] = []
        self.nodes = nodes
        self.in_text = False
        self.canonical = canonical

    def consume(self, raw: str):
        if not self.source.startswith(raw, self.cursor):
            raise TransformError("malformed_html")
        self.cursor += len(raw)

    def node(self, *, text=False):
        if not text or not self.in_text:
            self.nodes.charge()
        self.in_text = text

    def start(self, tag, attrs, *, closed):
        if tag == "plaintext":
            raise TransformError("malformed_html")
        raw = self.get_starttag_text()
        match = _TAG.match(raw)
        if match is None or match.group()[1:].lower() != tag:
            raise TransformError("malformed_html")
        index = match.end()
        while index < len(raw):
            before = index
            while index < len(raw) and raw[index] in "\t\n\r ":
                index += 1
            if raw[index:] in {">", "/>"}:
                break
            if index == before:
                raise TransformError("malformed_html")
            attribute = _ATTR.match(raw, index)
            if attribute is None:
                raise TransformError("malformed_html")
            attribute_references(attribute.group())
            index = attribute.end()
        else:
            raise TransformError("malformed_html")
        if len(attrs) > 32 or any(v is not None and len(v) > 4096 for _, v in attrs):
            raise TransformError("attribute_limit")
        if len({k for k, _ in attrs}) != len(attrs):
            raise TransformError("malformed_html")
        if closed and tag not in VOID:
            raise TransformError("malformed_html")
        if self.canonical and (tag not in ALLOWED or attrs or raw != f"<{tag}>"):
            raise TransformError("not_sanitized")
        if len(self.stack) + 1 > DEPTH_LIMIT:
            raise TransformError("depth_limit")
        self.consume(raw)
        self.node()
        self.open_tag(tag)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs, closed=False)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        match = _END.match(self.source, self.cursor)
        if match is None or match[1].lower() != tag or not self.stack or self.stack[-1] != tag:
            raise TransformError("malformed_html")
        raw = match.group()
        if self.canonical and raw != f"</{tag}>":
            raise TransformError("not_sanitized")
        self.consume(raw)
        self.in_text = False
        self.close_tag(tag)
        self.stack.pop()

    def handle_data(self, data):
        self.consume(data)
        if "<" in data and (not self.stack or self.stack[-1] not in {"script", "style"}):
            raise TransformError("malformed_html")
        if self.canonical and any(c in data for c in "&>"):
            raise TransformError("not_sanitized")
        self.node(text=True)
        self.text(data)

    def handle_entityref(self, name):
        self.consume(f"&{name};")
        if self.canonical and name not in {"amp", "lt", "gt"}:
            raise TransformError("not_sanitized")
        self.node(text=True)
        self.text(reference(name))

    def handle_charref(self, name):
        self.consume(f"&#{name};")
        if self.canonical:
            raise TransformError("not_sanitized")
        self.node(text=True)
        self.text(reference("#" + name))

    def handle_comment(self, data):
        if self.canonical:
            raise TransformError("not_sanitized")
        if "--" in data or data.endswith("-"):
            raise TransformError("malformed_html")
        self.consume("<!--" + data + "-->")
        self.node()

    def handle_decl(self, decl):
        raise TransformError("malformed_html")

    def unknown_decl(self, data):
        raise TransformError("malformed_html")

    def handle_pi(self, data):
        raise TransformError("malformed_html")

    def run(self):
        try:
            self.feed(self.source)
            self.close()
        except (AssertionError, ValueError) as error:
            if isinstance(error, TransformError):
                raise
            raise TransformError("malformed_html") from None
        if self.stack or self.cursor != len(self.source):
            raise TransformError("malformed_html")

    def open_tag(self, tag):
        raise NotImplementedError

    def close_tag(self, tag):
        raise NotImplementedError

    def text(self, data):
        raise NotImplementedError
