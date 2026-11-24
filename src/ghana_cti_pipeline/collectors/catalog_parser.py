"""Pure JSON envelope parsing; callers choose keys, future adapters map source schemas."""

import json
from dataclasses import dataclass, field
from decimal import Decimal

from ghana_cti_pipeline.collectors.parsing_values import (
    CATALOG_BYTES,
    MAX_DEPTH,
    PARSER_VERSION,
    ParseError,
    decode_input,
    metadata,
)


@dataclass(frozen=True)
class CatalogBatch:
    # Fresh ordinary JSON containers, not immutable persistence contracts.
    document: dict = field(repr=False)
    entries: tuple[dict, ...] = field(repr=False)
    parser_version: str = PARSER_VERSION


def _depth(text: str) -> None:
    """Bound container nesting before the standard decoder allocates nested objects."""
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise ParseError("depth_limit")
        elif char in "]}":
            depth -= 1  # Syntax, mismatched closers and trailing data checked by json.


def _object(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ParseError("duplicate_field")
        value[key] = child
    return value


def _constant(value):
    raise ParseError("invalid_json")


def _integer(value):
    # Explicit deterministic safety ceiling, independent of interpreter settings.
    if len(value.lstrip("-")) > 4300:
        raise ParseError("invalid_json")
    # Decimal avoids Python's configurable string-to-int digit limit.
    return int(Decimal(value))


def _check(value):
    if isinstance(value, str):
        metadata(value)
    elif isinstance(value, Decimal) and not value.is_finite():
        raise ParseError("invalid_json")
    elif isinstance(value, dict):
        for key, child in value.items():
            metadata(key)
            _check(child)
    elif isinstance(value, list):
        for child in value:
            _check(child)


def _same(left, right):
    """JSON field order is irrelevant; booleans and numbers are never interchangeable."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def parse_catalog(raw: bytes, *, entries_field: str, native_id_field: str) -> CatalogBatch:
    """Parse a nonempty object/list-of-entry envelope without discarding extension fields."""
    if any(
        type(key) is not str or not key.strip() or len(key) > 256
        for key in (entries_field, native_id_field)
    ):
        raise ParseError("configuration")
    text = decode_input(raw, CATALOG_BYTES)
    _depth(text)
    try:
        document = json.loads(
            text,
            object_pairs_hook=_object,
            parse_constant=_constant,
            parse_float=Decimal,
            parse_int=_integer,
        )
    except (ValueError, ArithmeticError, RecursionError) as error:
        if isinstance(error, ParseError):
            raise
        raise ParseError("invalid_json") from None
    _check(document)
    if not isinstance(document, dict):
        raise ParseError("envelope")
    entries = document.get(entries_field)
    if not isinstance(entries, list) or not entries:
        raise ParseError("envelope")
    if len(entries) > 10000:
        raise ParseError("item_limit")
    identities = {}
    for entry in entries:
        if not isinstance(entry, dict) or not entry:
            raise ParseError("envelope")
        native_id = entry.get(native_id_field)
        if type(native_id) is not str or not native_id.strip():
            raise ParseError("envelope")
        metadata(native_id, 256)
        if native_id in identities and not _same(identities[native_id], entry):
            raise ParseError("conflicting_id")
        identities[native_id] = entry
    return CatalogBatch(document, tuple(entries))
