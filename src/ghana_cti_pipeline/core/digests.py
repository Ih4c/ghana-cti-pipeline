"""Pure, bounded digest helpers. Domains qualify hashes; no input is parsed."""

import json
from hashlib import sha256
from typing import Literal, get_args

from ghana_cti_pipeline.core.evidence_values import SHA256, EvidenceContract

JSON_PROFILE = "cti-json-v1"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_INTEGER = 2**53 - 1
ContentDomain = Literal[
    "decoded-http-entity-v1",
    "feed-field-html-utf8-v1",
    "sanitized-html-utf8-v1",
    "plain-text-utf8-v1",
    "catalog-entry-json-v1",
    "evidence-metadata-json-v1",
    "processing-manifest-json-v1",
]


class ContentDigest(EvidenceContract):
    domain: ContentDomain
    sha256: SHA256


def _profile(profile: str) -> None:
    if type(profile) is not str or profile != JSON_PROFILE:
        raise ValueError("unsupported canonical JSON profile")


def canonical_json(value: object, *, profile: str = JSON_PROFILE) -> bytes:
    """Serialize the documented integer-only JSON profile without changing evidence."""
    _profile(profile)
    active: set[int] = set()
    remaining = MAX_JSON_BYTES

    def check(node: object, depth: int) -> None:
        nonlocal remaining
        remaining -= 1  # Lower bound on encoded size also bounds the traversal work.
        if remaining < 0:
            raise ValueError("canonical JSON exceeds byte limit")
        kind = type(node)
        if node is None or kind is bool:
            return
        if kind is int:
            if abs(node) > MAX_INTEGER:
                raise ValueError("integer outside canonical profile range")
        elif kind is str:
            remaining -= len(node)
            if remaining < 0:
                raise ValueError("canonical JSON exceeds byte limit")
            # Reject invalid Unicode without replacing evidence characters.
            node.encode("utf-8", errors="strict")
        elif kind in (dict, list):
            if depth >= MAX_JSON_DEPTH or id(node) in active:
                raise ValueError("canonical JSON nesting limit or cycle")
            if len(node) > remaining:
                raise ValueError("canonical JSON exceeds byte limit")
            active.add(id(node))
            try:
                if kind is dict:
                    for key, child in node.items():
                        if type(key) is not str:
                            raise ValueError("canonical object keys must be strings")
                        check(key, depth + 1)
                        check(child, depth + 1)
                else:
                    for child in node:
                        check(child, depth + 1)
            finally:
                active.remove(id(node))
        else:
            raise ValueError("unsupported canonical JSON value")

    check(value, 0)
    encoded = bytearray()
    encoder = json.JSONEncoder(
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    for chunk in encoder.iterencode(value):
        raw = chunk.encode("utf-8", errors="strict")
        if len(encoded) + len(raw) > MAX_JSON_BYTES:
            raise ValueError("canonical JSON exceeds byte limit")
        encoded.extend(raw)
    return bytes(encoded)


def compute_digest(
    domain: ContentDomain, value: object, *, profile: str = JSON_PROFILE
) -> ContentDigest:
    """Hash exact bytes/UTF-8/canonical JSON; return the mandatory domain/hash pair."""
    _profile(profile)
    if type(domain) is not str or domain not in get_args(ContentDomain):
        raise ValueError("unsupported digest domain")
    if domain == "decoded-http-entity-v1":
        if type(value) is not bytes:
            raise ValueError("decoded HTTP entity must be bytes")
        raw, limit = value, 8 * 1024 * 1024
    elif domain in {"feed-field-html-utf8-v1", "sanitized-html-utf8-v1", "plain-text-utf8-v1"}:
        if type(value) is not str:
            raise ValueError("text digest input must be an exact string")
        limit = 1024 * 1024
        if len(value) > limit:
            raise ValueError("text exceeds digest byte limit")
        raw = value.encode("utf-8", errors="strict")
    else:
        if type(value) is not dict:
            raise ValueError("structured digest input must be a JSON object")
        raw, limit = canonical_json(value, profile=profile), MAX_JSON_BYTES
    if len(raw) > limit:
        raise ValueError("input exceeds digest byte limit")
    return ContentDigest(domain=domain, sha256=sha256(raw).hexdigest())
