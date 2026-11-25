"""Versioned offline transformation profile and bounded, content-free failures."""

from io import StringIO

ARTICLE_LIMIT = 1024 * 1024
BATCH_LIMIT = 6 * ARTICLE_LIMIT
DEPTH_LIMIT = 64
NODE_LIMIT = 50000
SANITIZER_VERSION = "cti-inert-html-v1"
EXTRACTOR_VERSION = "cti-plain-text-v1"
HTML_PARSER_PROFILE = "cti-strict-html-fragment-v1"
ALLOWED = frozenset(
    {
        "p",
        "div",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "blockquote",
        "pre",
        "code",
        "strong",
        "em",
        "table",
        "caption",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
    }
)
UNWRAP = frozenset({"a", "span"})
VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
BLOCK = frozenset(
    {
        "p",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
        "table",
        "caption",
        "ul",
        "ol",
    }
)


class TransformError(ValueError):
    def __init__(self, code: str):
        if code not in {
            "invalid_input",
            "input_limit",
            "output_limit",
            "batch_limit",
            "item_limit",
            "invalid_character",
            "malformed_html",
            "depth_limit",
            "node_limit",
            "attribute_limit",
            "invalid_reference",
            "not_sanitized",
            "empty_output",
            "unsupported_version",
        }:
            raise ValueError("unsupported transformation error code")
        self.code = code
        super().__init__(code)


def characters(value: str) -> None:
    if any((ord(c) < 32 and c not in "\t\n\r") or 127 <= ord(c) <= 159 for c in value):
        raise TransformError("invalid_character")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError:
        raise TransformError("invalid_character") from None


def article(value: str) -> int:
    if type(value) is not str or not value:
        raise TransformError("invalid_input")
    if len(value) > ARTICLE_LIMIT:
        raise TransformError("input_limit")
    characters(value)
    if not value.strip():
        raise TransformError("invalid_input")
    size = len(value.encode("utf-8"))
    if size > ARTICLE_LIMIT:
        raise TransformError("input_limit")
    return size


class NodeBudget:
    def __init__(self):
        self.used = 0

    def charge(self):
        self.used += 1
        if self.used > NODE_LIMIT:
            raise TransformError("node_limit")


class Output:
    def __init__(self):
        self.buffer = StringIO()
        self.size = 0
        self.trailing_newlines = 0

    def write(self, value: str):
        size = len(value.encode("utf-8"))
        if self.size + size > ARTICLE_LIMIT:
            raise TransformError("output_limit")
        self.buffer.write(value)
        self.size += size
        if value:
            self.trailing_newlines = (
                self.trailing_newlines + len(value)
                if not value.strip("\n")
                else len(value) - len(value.rstrip("\n"))
            )

    def boundary(self, count: int):
        if self.size and self.trailing_newlines < count:
            self.write("\n" * (count - self.trailing_newlines))

    def finish(self, *, plain=False):
        result = self.buffer.getvalue()
        if plain:
            result = result.strip("\n")
        if not result.strip():
            raise TransformError("empty_output")
        return result
