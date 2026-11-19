"""Fixed SHA-256/canonical JSON vectors and bounded, strict input validation."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from ghana_cti_pipeline.core import identities
from ghana_cti_pipeline.core.digests import (
    MAX_INTEGER,
    MAX_JSON_BYTES,
    MAX_JSON_DEPTH,
    ContentDigest,
    canonical_json,
    compute_digest,
)

VECTORS = json.loads((Path(__file__).parent / "fixtures/identity_vectors.json").read_text("utf-8"))


@pytest.mark.parametrize("vector", VECTORS["canonical_json"])
def test_fixed_canonical_vectors(vector):
    encoded = canonical_json(vector["input"])
    assert encoded.hex() == vector["utf8_hex"]
    assert compute_digest("catalog-entry-json-v1", vector["input"]).sha256 == vector["sha256"]
    assert encoded == canonical_json(dict(reversed(list(vector["input"].items()))))


@pytest.mark.parametrize("vector", VECTORS["digests"], ids=lambda v: v["domain"])
def test_fixed_domain_vectors(vector):
    value = (
        bytes.fromhex(vector["input"])
        if vector["domain"] == "decoded-http-entity-v1"
        else vector["input"]
    )
    digest = compute_digest(vector["domain"], value)
    assert digest.sha256 == vector["sha256"]
    assert digest.domain == vector["domain"]
    assert ContentDigest.model_validate_json(digest.model_dump_json()) == digest
    with pytest.raises(ValidationError):
        digest.sha256 = "0" * 64
    with pytest.raises(ValidationError):
        digest.model_copy(update={"domain": "unsupported"})
    with pytest.raises(ValidationError):
        digest.model_copy(update={"sha256": "bad"}, deep=True)


def test_exact_byte_semantics_and_domain_separation():
    empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert compute_digest("decoded-http-entity-v1", b"").sha256 == empty
    assert compute_digest("plain-text-utf8-v1", "").sha256 == empty
    html = compute_digest("feed-field-html-utf8-v1", "abc")
    text = compute_digest("plain-text-utf8-v1", "abc")
    assert html.sha256 == text.sha256
    assert html != text  # The pair is the digest identity, never bare hex alone.
    for a, b in [("é", "e\u0301"), ("x\r\n", "x\n"), (" x", "x"), ("&amp;", "&"), ("Ａ", "A")]:
        assert compute_digest("feed-field-html-utf8-v1", a) != compute_digest(
            "feed-field-html-utf8-v1", b
        )


@pytest.mark.parametrize(
    "value",
    [
        1.0,
        -0.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        (1, 2),
        {1, 2},
        b"bytes",
        {1: "value"},
        object(),
    ],
)
def test_unsupported_json_values_reject(value):
    with pytest.raises(ValueError):
        canonical_json(value)


def test_json_scalar_types_missing_null_and_array_order():
    assert canonical_json(True) == b"true"
    assert canonical_json(1) == b"1"
    assert canonical_json(None) == b"null"
    assert canonical_json({}) != canonical_json({"x": None})
    assert canonical_json([1, 2]) != canonical_json([2, 1])
    assert canonical_json(MAX_INTEGER) == str(MAX_INTEGER).encode()
    assert canonical_json(-MAX_INTEGER) == str(-MAX_INTEGER).encode()
    for value in [MAX_INTEGER + 1, -MAX_INTEGER - 1]:
        with pytest.raises(ValueError):
            canonical_json(value)

    class String(str):
        pass

    class Integer(int):
        pass

    for value in [String("x"), Integer(1), {String("x"): 1}]:
        with pytest.raises(ValueError):
            canonical_json(value)


def test_json_cycle_depth_and_shared_noncyclic_values():
    cyclic = []
    cyclic.append(cyclic)
    with pytest.raises(ValueError):
        canonical_json(cyclic)
    mapping = {}
    mapping["self"] = mapping
    with pytest.raises(ValueError):
        canonical_json(mapping)
    shared = {"x": 1}
    assert canonical_json([shared, shared]) == b'[{"x":1},{"x":1}]'
    value = 0
    for _ in range(MAX_JSON_DEPTH):
        value = [value]
    canonical_json(value)
    with pytest.raises(ValueError):
        canonical_json([value])


def test_json_byte_boundary_and_no_surrogate_replacement():
    assert len(canonical_json("x" * (MAX_JSON_BYTES - 2))) == MAX_JSON_BYTES
    with pytest.raises(ValueError):
        canonical_json("x" * (MAX_JSON_BYTES - 1))
    for value in ["\ud800", {"\udfff": "x"}, {"x": "\ud800"}]:
        with pytest.raises(ValueError):
            canonical_json(value)
    with pytest.raises(ValueError):
        compute_digest("plain-text-utf8-v1", "\ud800")


@pytest.mark.parametrize(
    "domain", ["feed-field-html-utf8-v1", "sanitized-html-utf8-v1", "plain-text-utf8-v1"]
)
def test_utf8_byte_boundaries_not_character_counts(domain):
    assert compute_digest(domain, "é" * (1024 * 1024 // 2)).sha256
    with pytest.raises(ValueError):
        compute_digest(domain, "é" * (1024 * 1024 // 2) + "x")
    with pytest.raises(ValueError):
        compute_digest(domain, "x" * (1024 * 1024 + 1))
    for value in [b"text", None, 1]:
        with pytest.raises(ValueError):
            compute_digest(domain, value)


def test_response_bytes_and_structured_input_boundaries():
    assert compute_digest("decoded-http-entity-v1", b"x" * (8 * 1024 * 1024)).sha256
    for value in [b"x" * (8 * 1024 * 1024 + 1), "text", bytearray(b"x"), memoryview(b"x"), None]:
        with pytest.raises(ValueError):
            compute_digest("decoded-http-entity-v1", value)
    for domain in [
        "catalog-entry-json-v1",
        "evidence-metadata-json-v1",
        "processing-manifest-json-v1",
    ]:
        for value in ['{"a":1}', [], None, b"{}"]:
            with pytest.raises(ValueError):
                compute_digest(domain, value)


def test_unsupported_profiles_domains_and_no_input_mutation():
    value = {"z": ["é", True, None], "a": 1}
    before = json.dumps(value)
    canonical_json(value)
    assert json.dumps(value) == before
    for profile in ["unknown", "", None, 1]:
        with pytest.raises(ValueError):
            canonical_json(value, profile=profile)
        with pytest.raises(ValueError):
            compute_digest("catalog-entry-json-v1", value, profile=profile)
    for domain in ["wire-bytes", "sha256", "", None, 1, []]:
        with pytest.raises(ValueError):
            compute_digest(domain, b"abc")


def test_fixed_namespaces_and_cross_process_determinism():
    mapping = {
        "logical": "LOGICAL_NAMESPACE",
        "revision": "REVISION_NAMESPACE",
        "derived": "DERIVED_NAMESPACE",
        "artifact": "ARTIFACT_NAMESPACE",
        "association": "ASSOCIATION_NAMESPACE",
        "manifest": "MANIFEST_NAMESPACE",
        "observation": "OBSERVATION_NAMESPACE",
    }
    for key, name in mapping.items():
        assert str(getattr(identities, name)) == VECTORS["namespaces"][key]
    # Process launch/import I/O is test setup; helper no-I/O is checked separately.
    script = """from ghana_cti_pipeline.core.identities import logical_item_id
print(logical_item_id('synthetic-microsoft', {'kind':'native_id','value':'synthetic-guid-1'}))
"""
    expected = VECTORS["identities"][0]["expected"]["logical_item_id"]
    for seed in ["1", "917"]:
        result = subprocess.run(
            [sys.executable, "-c", script],
            env=os.environ | {"PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == expected
