"""Synthetic M1-01 acceptance tests; no source payloads or network access."""

import json
import socket
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from ghana_cti_pipeline.core.models import SourceItem
from ghana_cti_pipeline.core.retrieval import (
    ComputedDigest,
    EvidenceObservation,
    NotComputedDigest,
    NotModifiedResponse,
    ReceivedResponse,
    ResponseBodyMetadata,
    RetrievalFailure,
    RetrievalOutcome,
)

MODELS = {
    "body": ResponseBodyMetadata,
    "computed": ComputedDigest,
    "not_computed": NotComputedDigest,
    "received": ReceivedResponse,
    "not_modified": NotModifiedResponse,
    "failure": RetrievalFailure,
    "observation": EvidenceObservation,
}
OUTCOME = TypeAdapter(RetrievalOutcome)


@pytest.fixture
def examples():
    data = json.loads((Path(__file__).parent / "fixtures/retrieval.json").read_text("utf-8"))
    data["body"] = data["received"]["body_metadata"]
    data["computed"] = data["body"]["digest"]
    data["not_computed"] = {"digest_state": "not_computed"}
    return data


def reject(model, data, field=None):
    with pytest.raises(ValidationError) as caught:
        model.model_validate(data)
    if field:
        assert any(field in error["loc"] for error in caught.value.errors())


@pytest.mark.parametrize("key", MODELS)
def test_round_trip_frozen_versioned_records(examples, key):
    model = MODELS[key]
    record = model.model_validate(examples[key])
    assert model.model_validate_json(record.model_dump_json()) == record
    assert record.schema_version == "1.0"
    with pytest.raises(ValidationError, match="frozen"):
        record.schema_version = "2.0"


@pytest.mark.parametrize("key", ["received", "not_modified", "failure"])
def test_retrieval_union_dispatches_json_by_kind(examples, key):
    record = OUTCOME.validate_json(json.dumps(examples[key]))
    assert type(record) is MODELS[key]
    assert OUTCOME.validate_json(OUTCOME.dump_json(record)) == record


@pytest.mark.parametrize("tag", [None, "unknown", "evidence_observation", 200])
def test_union_requires_recognized_discriminator(examples, tag):
    data = examples["received"]
    if tag is None:
        del data["kind"]
    else:
        data["kind"] = tag
    with pytest.raises(ValidationError):
        OUTCOME.validate_json(json.dumps(data))


def test_discriminators_are_explicit_in_json_schema():
    assert OUTCOME.json_schema()["discriminator"]["propertyName"] == "kind"
    body_schema = ResponseBodyMetadata.model_json_schema()
    assert body_schema["properties"]["digest"]["discriminator"]["propertyName"] == "digest_state"


@pytest.mark.parametrize(
    "digest",
    [
        {"digest_state": "not_computed"},
        {"digest_state": "not_computed", "sha256": None, "domain": None},
    ],
)
def test_absent_digest_means_no_hash_or_domain(examples, digest):
    record = ReceivedResponse.model_validate(
        examples["received"] | {"body_metadata": examples["body"] | {"digest": digest}}
    )
    assert isinstance(record.body_metadata.digest, NotComputedDigest)
    assert record.body_metadata.digest.sha256 is None
    assert record.body_metadata.digest.domain is None


@pytest.mark.parametrize(
    "digest",
    [
        {},
        None,
        {"digest_state": "unknown"},
        {"digest_state": "computed"},
        {"digest_state": "computed", "sha256": None, "domain": "decoded-http-entity-v1"},
        {"digest_state": "computed", "sha256": "a" * 64},
        {"digest_state": "computed", "sha256": "a" * 64, "domain": "wire-bytes"},
        {"digest_state": "not_computed", "sha256": "a" * 64},
        {"digest_state": "not_computed", "domain": "decoded-http-entity-v1"},
    ],
)
def test_rejects_contradictory_digest_states(examples, digest):
    reject(ResponseBodyMetadata, examples["body"] | {"digest": digest}, "digest")


@pytest.mark.parametrize("digest", ["a" * 63, "a" * 65, "A" * 64, "g" * 64, "a" * 64 + "\n", 12])
def test_digest_is_exact_lowercase_sha256_text(examples, digest):
    reject(ComputedDigest, examples["computed"] | {"sha256": digest}, "sha256")


@pytest.mark.parametrize("key", MODELS)
@pytest.mark.parametrize("version", ["2.0", "", 1.0, None])
def test_unsupported_schema_versions_reject(examples, key, version):
    reject(MODELS[key], examples[key] | {"schema_version": version}, "schema_version")


@pytest.mark.parametrize("key", MODELS)
@pytest.mark.parametrize(
    "field,value",
    [
        ("body", "synthetic forbidden payload"),
        ("raw_bytes", b"synthetic bytes"),
        ("path", "/synthetic/not-a-real-file"),
        ("artifact_id", "synthetic-artifact"),
        ("raw_retained", True),
        ("headers", {"Authorization": "synthetic"}),
        ("exception_text", "synthetic failure payload"),
    ],
)
def test_extra_payload_retention_and_header_fields_reject(examples, key, field, value):
    reject(MODELS[key], examples[key] | {field: value}, field)


@pytest.mark.parametrize("key", ["not_modified", "failure", "observation"])
@pytest.mark.parametrize("field", ["body_metadata", "digest", "snapshot"])
def test_bodyless_records_cannot_embed_descriptors(examples, key, field):
    reject(MODELS[key], examples[key] | {field: examples["body"]}, field)


@pytest.mark.parametrize("key", ["received", "not_modified"])
@pytest.mark.parametrize("status", [199, 201, 302, 400, "200", "304", 200.0, 304.0, True, None])
def test_success_status_must_match_kind_and_be_integer(examples, key, status):
    reject(MODELS[key], examples[key] | {"status": status}, "status")
    with pytest.raises(ValidationError):
        OUTCOME.validate_json(json.dumps(examples[key] | {"status": status}))


def test_200_and_304_cannot_exchange_status(examples):
    reject(ReceivedResponse, examples["received"] | {"status": 304}, "status")
    reject(NotModifiedResponse, examples["not_modified"] | {"status": 200}, "status")


@pytest.mark.parametrize("status", [None, 100, 200, 304, 429, 503, 599])
def test_failure_preserves_received_status_without_claiming_success(examples, status):
    code = "body_limit" if status == 200 else "http_error" if status else "timeout"
    record = OUTCOME.validate_python(examples["failure"] | {"status": status, "code": code})
    assert isinstance(record, RetrievalFailure)
    assert record.status == status
    assert "body_metadata" not in record.model_dump()


@pytest.mark.parametrize("status", [99, 600, "503", 503.0, True])
def test_failure_status_boundaries_and_types(examples, status):
    reject(RetrievalFailure, examples["failure"] | {"status": status}, "status")


@pytest.mark.parametrize(
    "code",
    [
        "timeout",
        "connection_error",
        "tls_error",
        "unsafe_url",
        "redirect_limit",
        "proxy_disallowed",
        "header_limit",
        "body_limit",
        "content_decoding_error",
        "http_error",
        "protocol_error",
    ],
)
def test_only_declared_failure_codes_are_accepted(examples, code):
    assert RetrievalFailure.model_validate(examples["failure"] | {"code": code}).code == code


@pytest.mark.parametrize(
    "field,value",
    [
        ("code", "arbitrary exception"),
        ("code", ""),
        ("code", None),
        ("retryable", 1),
        ("retryable", 0),
        ("retryable", "true"),
        ("retryable", None),
    ],
)
def test_failure_vocabulary_and_retryability_are_strict(examples, field, value):
    reject(RetrievalFailure, examples["failure"] | {field: value}, field)


@pytest.mark.parametrize(
    "sent",
    [
        {"sent_etag": 'W/"synthetic"'},
        {"sent_last_modified": "Thu, 15 Jan 2026 10:00:00 GMT"},
        {"sent_etag": '"synthetic"', "sent_last_modified": "Thu, 15 Jan 2026 10:00:00 GMT"},
    ],
)
def test_304_accepts_either_or_both_sent_validators(examples, sent):
    data = examples["not_modified"] | {"sent_etag": None, "sent_last_modified": None} | sent
    assert NotModifiedResponse.model_validate(data).status == 304


def test_304_requires_sent_validator_not_just_returned_one(examples):
    reject(
        NotModifiedResponse,
        examples["not_modified"]
        | {
            "sent_etag": None,
            "sent_last_modified": None,
            "returned_etag": '"synthetic"',
        },
    )
    del examples["not_modified"]["representation_retrieval_id"]
    reject(NotModifiedResponse, examples["not_modified"], "representation_retrieval_id")


@pytest.mark.parametrize("field", ["decoded_bytes", "transferred_bytes"])
@pytest.mark.parametrize("value", [0, 8 * 1024 * 1024])
def test_byte_count_exact_limits(examples, field, value):
    assert (
        getattr(ResponseBodyMetadata.model_validate(examples["body"] | {field: value}), field)
        == value
    )


@pytest.mark.parametrize("field", ["decoded_bytes", "transferred_bytes"])
@pytest.mark.parametrize("value", [-1, 8 * 1024 * 1024 + 1, True, False, 1.0, "1", None])
def test_byte_count_bounds_and_coercion_reject(examples, field, value):
    reject(ResponseBodyMetadata, examples["body"] | {field: value}, field)


TEXT_LIMITS = [
    ("received", "source_id", 256),
    ("observation", "source_policy_id", 256),
    ("observation", "source_policy_version", 128),
    ("observation", "adapter_version", 128),
    ("observation", "locator", 4096),
    ("body", "media_type", 128),
    ("body", "content_encoding", 128),
    *[
        ("not_modified", field, 1024)
        for field in (
            "sent_etag",
            "sent_last_modified",
            "returned_etag",
            "returned_last_modified",
            "cache_control",
            "vary",
        )
    ],
]


@pytest.mark.parametrize("key,field,limit", TEXT_LIMITS)
def test_text_exact_limits_and_rejection_without_truncation(examples, key, field, limit):
    for value in ["x", "é" * limit]:
        record = MODELS[key].model_validate(examples[key] | {field: value})
        assert getattr(record, field) == value
    for invalid in ["x" * (limit + 1), "", " \t\n", "\u00a0", b"bytes", 123]:
        reject(MODELS[key], examples[key] | {field: invalid}, field)


@pytest.mark.parametrize(
    "field",
    [
        "sent_etag",
        "sent_last_modified",
        "returned_etag",
        "returned_last_modified",
        "cache_control",
        "vary",
    ],
)
@pytest.mark.parametrize("control", ["\r", "\n", "\t", "\x00", "\x7f", "\x85", "\u200b"])
def test_headers_reject_control_characters_before_use(examples, field, control):
    reject(NotModifiedResponse, examples["not_modified"] | {field: "a" + control + "b"}, field)


@pytest.mark.parametrize("field", ["authorization", "cookie", "set_cookie", "raw_headers"])
def test_http_header_allowlist_excludes_unapproved_fields(examples, field):
    reject(ReceivedResponse, examples["received"] | {field: "synthetic"}, field)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "http://example.org",
        "ftp://example.org",
        "https:example.org",
        "https:///example.org",
        "https://",
        "https://user:pass@example.org",
        "https://@example.org",
        "https://example.org/#",
        "https://example.org/#section",
        "https://example.org/a b",
        " https://example.org/",
        "https://example.org/\n",
        "https://example.org/\x85",
        "https://example.org/\u200b",
        "https://example.org/\\other",
        "https://example.org/%zz",
        "https://example.org:bad/",
        "https://[invalid/",
        "https://example.org:65536/",
    ],
)
@pytest.mark.parametrize("field", ["requested_url", "final_url", "redirect_urls"])
def test_malformed_url_fields_reject(examples, url, field):
    value = [url] if field == "redirect_urls" else url
    reject(ReceivedResponse, examples["received"] | {field: value}, field)


def test_url_limits_and_exact_preservation_without_dns(examples, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Descriptors must not resolve URLs")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    prefix = "https://example.org/"
    at_limit = prefix + "x" * (4096 - len(prefix))
    for url in ["HTTPS://Example.ORG:443/a?b=%2f&a=2", at_limit]:
        record = ReceivedResponse.model_validate(
            examples["received"]
            | {
                "requested_url": url,
                "final_url": url,
            }
        )
        assert record.requested_url == record.final_url == url
    for field in ["requested_url", "final_url", "redirect_urls"]:
        too_long = at_limit + "x"
        reject(
            ReceivedResponse,
            examples["received"]
            | {
                field: [too_long] if field == "redirect_urls" else too_long,
            },
            field,
        )


def test_redirect_chain_limits_and_final_destination(examples):
    redirects = [f"https://example.org/hop-{i}" for i in range(3)]
    record = ReceivedResponse.model_validate(
        examples["received"]
        | {
            "redirect_urls": redirects,
            "final_url": redirects[-1],
        }
    )
    redirects.append("https://example.org/hop-4")
    assert len(record.redirect_urls) == 3  # Input list cannot mutate the frozen record.
    reject(
        ReceivedResponse,
        examples["received"]
        | {
            "redirect_urls": redirects,
            "final_url": redirects[-1],
        },
        "redirect_urls",
    )
    reject(ReceivedResponse, examples["received"] | {"final_url": "https://example.org/other"})
    reject(ReceivedResponse, examples["received"] | {"redirect_urls": redirects[:1]})


@pytest.mark.parametrize("key", ["received", "not_modified", "failure"])
@pytest.mark.parametrize("field", ["started_at", "ended_at"])
@pytest.mark.parametrize(
    "value",
    [
        1768473000,
        1768473000.5,
        "1768473000",
        "1768473000.5",
        True,
        "2026-01-15",
        "2026-01-15T10:30:00",
        "2026-02-30T10:30:00Z",
        datetime(2026, 1, 15, 10, 30),
        None,
    ],
)
def test_timestamps_reject_epochs_naive_and_invalid_values(examples, key, field, value):
    reject(MODELS[key], examples[key] | {field: value}, field)


def test_timestamp_order_uses_offsets_and_accepts_equal_instants(examples):
    for start, end in [
        ("2026-01-15T11:30:00+01:00", "2026-01-15T10:30:00Z"),
        (datetime(2026, 1, 15, 10, 30, tzinfo=UTC), "2026-01-15T11:30:00+0100"),
    ]:
        record = ReceivedResponse.model_validate(
            examples["received"]
            | {
                "started_at": start,
                "ended_at": end,
            }
        )
        assert record.started_at == record.ended_at
    reject(ReceivedResponse, examples["received"] | {"ended_at": "2026-01-15T09:30:00Z"})


ID_FIELDS = [
    ("received", "retrieval_id"),
    ("not_modified", "retrieval_id"),
    ("not_modified", "representation_retrieval_id"),
    ("failure", "retrieval_id"),
    ("observation", "observation_id"),
    ("observation", "retrieval_id"),
    ("observation", "evidence_id"),
]


@pytest.mark.parametrize("key,field", ID_FIELDS)
def test_ids_are_required_caller_supplied_uuids(examples, key, field):
    data = examples[key].copy()
    del data[field]
    reject(MODELS[key], data, field)
    for invalid in ["", "not-a-uuid", 1, None]:
        reject(MODELS[key], examples[key] | {field: invalid}, field)
    valid = UUID(examples[key][field])
    assert getattr(MODELS[key].model_validate(examples[key] | {field: valid}), field) == valid


@pytest.mark.parametrize("kind,version", [("v1", "1.0"), ("hybrid", "2.0")])
def test_declared_evidence_reference_versions(examples, kind, version):
    record = EvidenceObservation.model_validate(
        examples["observation"]
        | {
            "evidence_kind": kind,
            "evidence_schema_version": version,
        }
    )
    assert record.schema_version == "1.0"  # Reference version is not the observation schema.
    assert record.evidence_schema_version == version


@pytest.mark.parametrize(
    "kind,version",
    [
        ("v1", "2.0"),
        ("hybrid", "1.0"),
        ("unknown", "1.0"),
        ("hybrid", "3.0"),
        ("v1", 1.0),
    ],
)
def test_evidence_kind_version_mismatches_reject(examples, kind, version):
    reject(
        EvidenceObservation,
        examples["observation"]
        | {
            "evidence_kind": kind,
            "evidence_schema_version": version,
        },
    )


@pytest.mark.parametrize("key", MODELS)
@pytest.mark.parametrize("deep", [False, True])
def test_copy_revalidates_extras_versions_and_preserves_original(examples, key, deep):
    record = MODELS[key].model_validate(examples[key])
    original = record.model_dump_json()
    for update in [{"schema_version": "9.0"}, {"raw_bytes": "synthetic"}]:
        with pytest.raises(ValidationError):
            record.model_copy(update=update, deep=deep)
    assert record.model_copy(deep=deep) == record
    assert record.model_dump_json() == original


@pytest.mark.parametrize("deep", [False, True])
def test_copy_revalidates_nested_values_and_valid_updates(examples, deep):
    record = ReceivedResponse.model_validate(examples["received"])
    invalid_body = examples["body"] | {"decoded_bytes": -1}
    with pytest.raises(ValidationError):
        record.model_copy(update={"body_metadata": invalid_body}, deep=deep)
    copied = record.model_copy(update={"source_id": "other-synthetic-source"}, deep=deep)
    assert copied.source_id == "other-synthetic-source"
    assert record.source_id == "synthetic-source"
    reject(
        ReceivedResponse,
        examples["received"]
        | {
            "body_metadata": ResponseBodyMetadata.model_construct(**invalid_body),
        },
    )


@pytest.mark.parametrize("excerpt", [None, "", " \t\n"])
def test_v1_excerpt_requirement_is_not_weakened(records, excerpt):
    data = records["source_item"].copy()
    if excerpt is None:
        del data["excerpt"]
    else:
        data["excerpt"] = excerpt
    reject(SourceItem, data, "excerpt")


def test_v1_fixture_shape_and_reference_semantics_stay_unchanged(records):
    data = records["source_item"]
    item = SourceItem.model_validate(data)
    dumped = item.model_dump(mode="json")
    assert set(dumped) == set(data)
    assert set(dumped["provenance"]) == set(data["provenance"])
    assert (
        item.provenance.original_url == data["provenance"]["original_url"]
    )  # V1 permits fragments.
    assert item.excerpt == data["excerpt"]
    assert SourceItem.model_validate_json(item.model_dump_json()) == item


def test_existing_network_guard_is_active():
    with pytest.raises(AssertionError, match="Network access is forbidden"):
        socket.create_connection(("example.org", 443))


@pytest.mark.parametrize("deep", [False, True])
@pytest.mark.parametrize(
    "key,update",
    [
        ("received", {"status": 304}),
        ("received", {"ended_at": "2026-01-15T09:30:00Z"}),
        ("received", {"final_url": "https://example.org/wrong"}),
        ("not_modified", {"sent_etag": None, "sent_last_modified": None}),
        ("observation", {"evidence_kind": "hybrid"}),
        ("computed", {"digest_state": "not_computed"}),
        ("not_computed", {"sha256": "a" * 64}),
    ],
)
def test_copy_revalidates_discriminators_and_cross_field_rules(examples, key, update, deep):
    record = MODELS[key].model_validate(examples[key])
    with pytest.raises(ValidationError):
        record.model_copy(update=update, deep=deep)


@pytest.mark.parametrize("key", ["body", "received", "not_modified", "failure", "observation"])
def test_each_contract_requires_its_exact_kind(examples, key):
    data = examples[key].copy()
    del data["kind"]
    reject(MODELS[key], data, "kind")
    reject(MODELS[key], data | {"kind": "unknown"}, "kind")
