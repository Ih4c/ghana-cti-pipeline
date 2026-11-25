"""Pure bounded RSS 2.0 field extraction. HTML stays inert and unparsed."""

import json
from hashlib import sha256
from io import StringIO
from xml.parsers import expat

from ghana_cti_pipeline.collectors.parsing_values import (
    ARTICLE_BYTES,
    MAX_DEPTH,
    RSS_BYTES,
    ParseError,
    RSSBatch,
    RSSItem,
    XMLField,
    decode_input,
    metadata,
)

_DC = "http://purl.org/dc/elements/1.1/"
_FIELDS = {
    "guid": 256,
    "link": 4096,
    "title": 512,
    "pubDate": 8192,
    "author": 256,
    "source": 256,
    "description": 65536,
    f"{_DC}|creator": 256,
    f"{_DC}|publisher": 256,
    f"{_DC}|date": 8192,
}


def parse_rss(raw: bytes, *, body_namespace: str, body_local_name: str) -> RSSBatch:
    """Return all items only after the complete document succeeds; no partial batch."""
    if (
        type(body_namespace) is not str
        or type(body_local_name) is not str
        or len(body_namespace) > 4096
        or not body_local_name
        or len(body_local_name) > 256
        or any(c in body_namespace + body_local_name for c in "|\x00")
        or ":" in body_local_name
    ):
        raise ParseError("configuration")
    body_name = f"{body_namespace}|{body_local_name}" if body_namespace else body_local_name
    if body_name in _FIELDS and body_name != "description":
        raise ParseError("configuration")
    decode_input(raw, RSS_BYTES)  # Reject UTF-16/autodetection before invoking Expat.
    parser = expat.ParserCreate(encoding="UTF-8", namespace_separator="|")
    stack: list[str] = []
    channel: dict[str, XMLField] = {}
    items: list[RSSItem] = []
    fields: dict[str, XMLField] | None = None
    body: XMLField | None = None
    capture: tuple[str, dict[str, str], StringIO] | None = None
    capture_size = 0
    digest = None
    identities: dict[str, bytes] = {}
    channels = 0
    aggregate = 0

    def reject(*args):
        raise ParseError("unsafe_xml")

    def declaration(version, encoding, standalone):
        if version != "1.0" or (encoding is not None and encoding.lower() != "utf-8"):
            raise ParseError("encoding")

    def event(kind, value):
        if digest is not None:
            # NUL cannot occur in legal XML text, so these structural delimiters
            # cannot collide with text. Chunk boundaries and CDATA do not matter.
            digest.update(b"\x00" + json.dumps([kind, value], sort_keys=True).encode() + b"\x00")

    def start(name, attrs):
        nonlocal channels, fields, body, digest, capture, capture_size
        if len(stack) >= MAX_DEPTH:
            raise ParseError("depth_limit")
        metadata(name)
        for key, value in attrs.items():
            metadata(key)
            metadata(value, 4096 if key == "url" else 8192)
        if name.startswith("http://www.w3.org/2001/XInclude|"):
            reject()
        if not stack:
            if name != "rss" or attrs.get("version") != "2.0":
                raise ParseError("envelope")
        elif len(stack) == 1:
            if name != "channel" or channels:
                raise ParseError("envelope")
            channels += 1
        elif name == "item":
            if stack != ["rss", "channel"]:
                raise ParseError("envelope")
            if len(items) >= 500:
                raise ParseError("item_limit")
            fields, body, digest = {}, None, sha256()
        if capture is not None:
            # Never flatten nested markup into a supposedly complete original field.
            raise ParseError("required_body" if capture[0] == body_name else "envelope")
        event("start", [name, attrs])
        if (stack == ["rss", "channel", "item"] and (name in _FIELDS or name == body_name)) or (
            stack == ["rss", "channel"] and name in _FIELDS
        ):
            capture = (name, attrs, StringIO())
            capture_size = 0
        stack.append(name)

    def text(value):
        nonlocal capture_size
        if digest is not None:
            digest.update(value.encode("utf-8"))
        if capture is not None:
            name, attrs, buffer = capture
            is_body = fields is not None and name == body_name
            capture_size += len(value.encode("utf-8")) if is_body else len(value)
            limit = ARTICLE_BYTES if is_body else _FIELDS[name]
            if name == "guid":
                limit = 4096
            if capture_size > limit:
                raise ParseError("field_limit")
            buffer.write(value)
        elif (
            value.strip()
            and len(stack) <= 3
            and (not stack or stack[-1] in {"rss", "channel", "item"})
        ):
            raise ParseError("envelope")

    def end(name):
        nonlocal capture, body, fields, digest, aggregate
        event("end", name)
        if capture is not None:
            field_name, attrs, buffer = capture
            namespace, _, local = field_name.rpartition("|")
            value = buffer.getvalue()
            parsed = XMLField(namespace, local, value, tuple(sorted(attrs.items())))
            if fields is not None and field_name == body_name:
                if body is not None:
                    raise ParseError("duplicate_field")
                if not value.strip():
                    raise ParseError("required_body")
                body = parsed
                aggregate += len(value.encode("utf-8"))
                if aggregate > RSS_BYTES:
                    raise ParseError("field_limit")
            else:
                target = channel if fields is None else fields
                if field_name in target:
                    raise ParseError("duplicate_field")
                if field_name == "guid":
                    if (
                        attrs.get("isPermaLink", "true") not in {"true", "false"}
                        or not value.strip()
                    ):
                        raise ParseError("envelope")
                    # Only actual HTTP(S) URL GUIDs get the URL-sized allowance.
                    if not value.startswith(("http://", "https://")):
                        metadata(value, 256)
                target[field_name] = parsed
            capture = None
        if name == "item":
            if body is None:
                raise ParseError("required_body")
            assert fields is not None and digest is not None
            guid = fields.get("guid")
            if guid is not None:
                fingerprint = digest.digest()
                if guid.value in identities and identities[guid.value] != fingerprint:
                    raise ParseError("conflicting_id")
                identities[guid.value] = fingerprint
            items.append(RSSItem(len(items), tuple(fields.values()), body))
            fields, body, digest = None, None, None
        stack.pop()

    parser.XmlDeclHandler = declaration
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = text
    parser.StartDoctypeDeclHandler = reject
    parser.EntityDeclHandler = reject
    parser.ExternalEntityRefHandler = reject
    parser.SkippedEntityHandler = reject
    parser.ProcessingInstructionHandler = reject
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(raw, True)
    except expat.ExpatError:
        raise ParseError("invalid_xml") from None
    if channels != 1 or any(
        not channel.get(key) or not channel[key].value.strip()
        for key in ("title", "link", "description")
    ):
        raise ParseError("envelope")
    return RSSBatch(tuple(channel.values()), tuple(items))
