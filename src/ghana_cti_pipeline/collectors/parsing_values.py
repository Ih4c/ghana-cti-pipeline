"""Private, pure parsing bounds and safe errors; no transport or storage dependency."""

from dataclasses import dataclass, field

RSS_BYTES = 6 * 1024 * 1024
CATALOG_BYTES = 8 * 1024 * 1024
ARTICLE_BYTES = 1024 * 1024
MAX_DEPTH = 64
PARSER_VERSION = "m1-safe-parsing-v1"


class ParseError(ValueError):
    """Only a finite code is safe to log; no input or underlying parser exception."""

    def __init__(self, code: str):
        if code not in {
            "invalid_input",
            "input_limit",
            "encoding",
            "unsafe_xml",
            "invalid_xml",
            "invalid_json",
            "envelope",
            "depth_limit",
            "item_limit",
            "field_limit",
            "required_body",
            "duplicate_field",
            "conflicting_id",
            "configuration",
        }:
            raise ValueError("unsupported parse error code")
        self.code = code
        super().__init__(code)


def decode_input(raw: bytes, limit: int) -> str:
    if type(raw) is not bytes or not raw:
        raise ParseError("invalid_input")
    if len(raw) > limit:
        raise ParseError("input_limit")
    try:
        return raw.decode("utf-8-sig", errors="strict")
    except UnicodeError:
        raise ParseError("encoding") from None


def metadata(value: str, limit: int = 8192) -> str:
    if len(value) > limit:
        raise ParseError("field_limit")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise ParseError("encoding") from None
    return value


@dataclass(frozen=True)
class XMLField:
    """Expanded name and XML-decoded text; attributes remain inert supplied values."""

    namespace: str
    local_name: str
    value: str = field(repr=False)
    attributes: tuple[tuple[str, str], ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class RSSItem:
    index: int
    fields: tuple[XMLField, ...] = field(repr=False)
    body: XMLField = field(repr=False)


@dataclass(frozen=True)
class RSSBatch:
    channel_fields: tuple[XMLField, ...] = field(repr=False)
    items: tuple[RSSItem, ...] = field(repr=False)
    parser_version: str = PARSER_VERSION
