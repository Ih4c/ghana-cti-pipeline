"""Synthetic-only contract tests: no source payloads, parsers or hash computation."""

import copy
import json
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from ghana_cti_pipeline.core.artifacts import (
    ArtifactAvailability,
    ArtifactParent,
    ArtifactReference,
    CatalogEntryArtifact,
    OriginalHTMLArtifact,
    PlainTextArtifact,
    ResponseArtifact,
    SanitizedHTMLArtifact,
    Transformation,
)
from ghana_cti_pipeline.core.evidence import (
    CatalogContext,
    CatalogEvidenceRevision,
    CatalogFields,
    EvidenceMetadataDigest,
    EvidenceProvenance,
    EvidenceRevisionV2,
    FeedFullTextEvidenceRevision,
    NativeKey,
    PublicationDate,
    URLKey,
)
from ghana_cti_pipeline.core.evidence_values import (
    SHA256,
    CalendarDate,
    Identifier,
    Locator,
    Metadata,
    PolicyReference,
    ReferenceURL,
    Timestamp,
    Version,
)
from ghana_cti_pipeline.core.processing import (
    FeedManifestItem,
    ManifestDigest,
    ProcessingManifest,
)
from ghana_cti_pipeline.core.source_policy import RetentionDeadlines, SourcePolicy

EVIDENCE = TypeAdapter(EvidenceRevisionV2)
ARTIFACT = TypeAdapter(ArtifactReference)
FIXTURE = Path(__file__).parent / "fixtures/evidence_v2.json"


@pytest.fixture
def examples():
    return json.loads(FIXTURE.read_text("utf-8"))


def nested(data, path):
    for key in path.split("."):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def replace(data, path, value):
    result = copy.deepcopy(data)
    parts = path.split(".")
    target = result
    for key in parts[:-1]:
        target = target[int(key)] if isinstance(target, list) else target[key]
    key = int(parts[-1]) if isinstance(target, list) else parts[-1]
    target[key] = value
    return result


MODELS = [
    ("microsoft", FeedFullTextEvidenceRevision),
    ("google", FeedFullTextEvidenceRevision),
    ("catalog", CatalogEvidenceRevision),
    ("policy", SourcePolicy),
    ("manifest", ProcessingManifest),
    ("availability", ArtifactAvailability),
    ("microsoft.provenance", EvidenceProvenance),
    ("microsoft.provenance.policy", PolicyReference),
    ("microsoft.provenance.publication", PublicationDate),
    ("microsoft.provenance.source_key", NativeKey),
    ("google.provenance.source_key", URLKey),
    ("catalog.catalog", CatalogContext),
    ("microsoft.metadata_digest", EvidenceMetadataDigest),
    ("catalog.fields", CatalogFields),
    ("microsoft.response", ResponseArtifact),
    ("microsoft.original", OriginalHTMLArtifact),
    ("microsoft.sanitized", SanitizedHTMLArtifact),
    ("microsoft.plain_text", PlainTextArtifact),
    ("catalog.entry", CatalogEntryArtifact),
    ("microsoft.original.parent", ArtifactParent),
    ("microsoft.sanitized.transformation", Transformation),
    ("policy.retention", RetentionDeadlines),
    ("manifest.items.0", FeedManifestItem),
    ("manifest.digest", ManifestDigest),
]


@pytest.mark.parametrize("path,model", MODELS)
def test_all_contracts_round_trip_frozen_copy_and_reject_extra_versions(examples, path, model):
    data = nested(examples, path)
    record = model.model_validate(data)
    original = record.model_dump_json()
    assert model.model_validate_json(original) == record
    with pytest.raises(ValidationError, match="frozen"):
        record.schema_version = "99.0"
    for update in [
        {"schema_version": "99.0"},
        {"raw_body": "forbidden synthetic body"},
        {"path": "/synthetic"},
        {"permission_verified": True},
    ]:
        with pytest.raises(ValidationError):
            model.model_validate(data | update)
        for deep in (False, True):
            with pytest.raises(ValidationError):
                record.model_copy(update=update, deep=deep)
    assert record.model_copy(deep=True) == record
    assert record.model_dump_json() == original


@pytest.mark.parametrize("key", ["catalog", "microsoft", "google"])
def test_discriminated_evidence_and_defaults(examples, key):
    record = EVIDENCE.validate_json(json.dumps(examples[key]))
    assert record.kind == "hybrid"
    assert record.schema_version == "2.0"
    assert record.confidence == "unknown"
    assert record.tlp is None
    assert EVIDENCE.validate_json(EVIDENCE.dump_json(record)) == record
    for update in [
        {"mode": "metadata_only"},
        {"mode": "unknown"},
        {"kind": "v1"},
        {"schema_version": "1.0"},
        {"confidence": "high"},
        {"ghana_relevance": "confirmed_targeting"},
    ]:
        with pytest.raises(ValidationError):
            EVIDENCE.validate_python(examples[key] | update)
    data = examples[key].copy()
    del data["mode"]
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(data)


@pytest.mark.parametrize("key", ["original", "sanitized", "plain_text", "response"])
def test_full_text_requires_all_backing_descriptors(examples, key):
    data = examples["microsoft"]
    del data[key]
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(data)
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(data | {key: None})


@pytest.mark.parametrize(
    "path",
    [
        "microsoft.response",
        "microsoft.original",
        "microsoft.sanitized",
        "microsoft.plain_text",
        "catalog.entry",
    ],
)
def test_artifact_kind_domain_and_body_exclusions(examples, path):
    data = nested(examples, path)
    assert ARTIFACT.validate_json(json.dumps(data)).kind == data["kind"]
    for update in [
        {"digest_domain": "wire-bytes"},
        {"kind": "metadata"},
        {"body": "<p>synthetic</p>"},
        {"storage_path": "/synthetic"},
        {"sha256": "A" * 64},
        {"sha256": "a" * 63},
        {"byte_count": True},
        {"byte_count": 1.0},
    ]:
        with pytest.raises(ValidationError):
            ARTIFACT.validate_python(data | update)
    # A valid domain for a different representation must also fail.
    wrong = (
        "feed-field-html-utf8-v1" if data["kind"] == "http_response" else "decoded-http-entity-v1"
    )
    with pytest.raises(ValidationError):
        ARTIFACT.validate_python(data | {"digest_domain": wrong})


@pytest.mark.parametrize(
    "path,value",
    [
        ("original.parent.kind", "original_html"),
        ("original.parent.sha256", "0" * 64),
        ("sanitized.parent.artifact_id", "00000000-0000-4000-8000-000000000999"),
        ("plain_text.parent.digest_domain", "feed-field-html-utf8-v1"),
        ("original.policy.policy_version", "other"),
        ("response.policy.source_id", "other"),
        ("sanitized.transformation.operation", "extract_text"),
        ("plain_text.transformation.operation", "sanitize_html"),
        ("original.locator", "/wrong"),
        ("original.source_field", "summary"),
        ("provenance.source_id", "other"),
        ("provenance.original_url", None),
        ("provenance.first_acquisition.status", 304),
        ("provenance.byline", "Synthetic byline without origin"),
        ("response.retrieval_id", "00000000-0000-4000-8000-000000000999"),
        ("response.sha256", "0" * 64),
        ("response.byte_count", 101),
    ],
)
def test_invalid_relationships_reject_including_copy_updates(examples, path, value):
    data = replace(examples["microsoft"], path, value)
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(data)
    original = EVIDENCE.validate_python(examples["microsoft"])
    field = path.split(".")[0]
    for deep in (False, True):
        with pytest.raises(ValidationError):
            original.model_copy(update={field: data[field]}, deep=deep)


def test_duplicate_and_self_parent_ids_reject(examples):
    data = examples["microsoft"]
    data["original"]["artifact_id"] = data["response"]["artifact_id"]
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(data)


def test_url_key_exactness_and_native_id_rules(examples):
    data = examples["google"]
    value = data["provenance"]["original_url"]
    assert EVIDENCE.validate_python(data).provenance.source_key.value == value
    data["provenance"]["source_key"]["value"] = "https://example.org/different"
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(data)
    for key, value in [
        ("source_key", {"kind": "original_url", "value": "https://example.org/"}),
        ("locator", "/wrong"),
    ]:
        bad = replace(examples["catalog"], "provenance." + key, value)
        with pytest.raises(ValidationError):
            EVIDENCE.validate_python(bad)


@pytest.mark.parametrize(
    "data",
    [
        {"precision": "unknown", "parse_outcome": "missing"},
        {"precision": "unknown", "parse_outcome": "invalid", "supplied_text": "not a date"},
        {"precision": "unknown", "parse_outcome": "invalid", "supplied_text": ""},
        {"precision": "unknown", "parse_outcome": "invalid", "supplied_text": "2026-02-30"},
        {
            "precision": "date",
            "parse_outcome": "parsed",
            "supplied_text": "2026-01-15",
            "date": "2026-01-15",
        },
        {
            "precision": "timestamp",
            "parse_outcome": "parsed",
            "supplied_text": "Thu, 15 Jan 2026 12:00:00 +0100",
            "timestamp": "2026-01-15T12:00:00+01:00",
        },
    ],
)
def test_publication_precision_preserves_supplied_text(data):
    record = PublicationDate.model_validate(data)
    assert record.supplied_text == data.get("supplied_text")
    assert PublicationDate.model_validate_json(record.model_dump_json()) == record


@pytest.mark.parametrize(
    "update",
    [
        {"precision": "date"},
        {"parse_outcome": "parsed"},
        {"date": "2026-01-15"},
        {"timestamp": "2026-01-15T00:00:00Z"},
        {"parse_outcome": "invalid"},
        {"supplied_text": "2026-01-15"},
        {"precision": "year"},
    ],
)
def test_unknown_date_cannot_invent_parsed_values(update):
    with pytest.raises(ValidationError):
        PublicationDate.model_validate(
            {"precision": "unknown", "parse_outcome": "missing"} | update
        )


@pytest.mark.parametrize(
    "value",
    ["2026-02-30", "2026-01-15T00:00:00Z", 1768435200, True, datetime(2026, 1, 15, tzinfo=UTC)],
)
def test_calendar_dates_reject_invalid_dates_and_coercion(value):
    with pytest.raises(ValidationError):
        TypeAdapter(CalendarDate).validate_python(value)


def test_dates_do_not_relabel_catalog_deadlines_as_publication(examples):
    record = EVIDENCE.validate_python(examples["catalog"])
    assert record.fields.dateAdded == date(2026, 1, 14)
    assert record.fields.dueDate == date(2026, 2, 1)
    assert record.provenance.publication.precision == "unknown"


@pytest.mark.parametrize(
    "value",
    [1, 1.2, "1768435200", "2026-01-15", "2026-01-15T00:00:00", datetime(2026, 1, 15), True],
)
def test_explicit_offset_timestamps_only(value):
    with pytest.raises(ValidationError):
        TypeAdapter(Timestamp).validate_python(value)


@pytest.mark.parametrize(
    "annotation,limit", [(Identifier, 256), (Version, 128), (Metadata, 8192), (Locator, 4096)]
)
def test_exact_shared_text_limits(annotation, limit):
    adapter = TypeAdapter(annotation)
    for value in ["x", "é" * limit]:
        assert adapter.validate_python(value) == value
    for value in ["", " \t\n", "x" * (limit + 1), b"bytes", 1, None]:
        with pytest.raises(ValidationError):
            adapter.validate_python(value)


def test_exact_hash_and_url_limits():
    assert TypeAdapter(SHA256).validate_python("a" * 64) == "a" * 64
    for bad in ["a" * 63, "a" * 65, "A" * 64, "z" * 64, "a" * 64 + "\n", b"a" * 64]:
        with pytest.raises(ValidationError):
            TypeAdapter(SHA256).validate_python(bad)
    prefix = "https://example.org/"
    maximum = prefix + "x" * (4096 - len(prefix))
    for url in [maximum, "http://Example.ORG/a?b=%2f&a=1#ref"]:
        assert TypeAdapter(ReferenceURL).validate_python(url) == url
    for url in [
        maximum + "x",
        "https://user@example.org",
        "https://@example.org",
        "https:///example.org",
        "javascript:alert(1)",
        "https://example.org/\n",
        "https://example.org/\u200b",
        "https://example.org/a b",
        "https://example.org/%xy",
        "https://example.org/\\x",
        1,
        b"https://example.org/",
    ]:
        with pytest.raises(ValidationError):
            TypeAdapter(ReferenceURL).validate_python(url)


@pytest.mark.parametrize(
    "path,maximum,minimum",
    [
        ("microsoft.response", 8 * 1024 * 1024, 0),
        ("catalog.entry", 8 * 1024 * 1024, 1),
        ("microsoft.original", 1024 * 1024, 1),
        ("microsoft.sanitized", 1024 * 1024, 1),
        ("microsoft.plain_text", 1024 * 1024, 1),
    ],
)
def test_artifact_byte_boundaries(examples, path, maximum, minimum):
    data = nested(examples, path)
    for value in [minimum, maximum]:
        assert ARTIFACT.validate_python(data | {"byte_count": value}).byte_count == value
    for value in [minimum - 1, maximum + 1, True, False, "1", 1.0]:
        with pytest.raises(ValidationError):
            ARTIFACT.validate_python(data | {"byte_count": value})


@pytest.mark.parametrize(
    "path",
    [
        "evidence_id",
        "logical_item_id",
        "response.artifact_id",
        "response.retrieval_id",
        "original.parent.artifact_id",
    ],
)
def test_identity_references_require_uuids(examples, path):
    for value in ["not-uuid", 1, None]:
        with pytest.raises(ValidationError):
            EVIDENCE.validate_python(replace(examples["microsoft"], path, value))


def test_nested_unchecked_instance_is_revalidated(examples):
    data = examples["microsoft"]["original"] | {"byte_count": -1}
    unchecked = OriginalHTMLArtifact.model_construct(**data)
    with pytest.raises(ValidationError):
        EVIDENCE.validate_python(examples["microsoft"] | {"original": unchecked})


def test_valid_copies_do_not_mutate_input_and_input_lists_are_frozen(examples):
    record = EVIDENCE.validate_python(examples["catalog"])
    examples["catalog"]["fields"]["cwes"].append("CWE-SYNTHETIC")
    assert record.fields.cwes == ("CWE-000",)
    for deep in (False, True):
        updated = record.model_copy(
            update={"evidence_id": UUID("00000000-0000-4000-8000-000000000998")}, deep=deep
        )
        assert updated.evidence_id != record.evidence_id
        assert updated.provenance == record.provenance


def test_v1_and_m1_01_fixtures_remain_compatible(records):
    from ghana_cti_pipeline.core.models import SourceItem
    from ghana_cti_pipeline.core.retrieval import EvidenceObservation, RetrievalOutcome

    SourceItem.model_validate(records["source_item"])
    data = json.loads((FIXTURE.parent / "retrieval.json").read_text("utf-8"))
    for key in ("received", "not_modified", "failure"):
        value = TypeAdapter(RetrievalOutcome).validate_python(data[key])
        assert TypeAdapter(RetrievalOutcome).validate_json(value.model_dump_json()) == value
    obs = EvidenceObservation.model_validate(
        data["observation"] | {"evidence_kind": "hybrid", "evidence_schema_version": "2.0"}
    )
    assert obs.schema_version == "1.0"


@pytest.mark.parametrize("field", ["decoded_bytes", "transferred_bytes"])
def test_feed_evidence_enforces_response_cap(examples, field):
    data = examples["microsoft"]
    data["provenance"]["first_acquisition"]["body_metadata"][field] = 6 * 1024 * 1024
    if field == "decoded_bytes":
        data["response"]["byte_count"] = 6 * 1024 * 1024
    record = EVIDENCE.validate_python(data)
    assert EVIDENCE.validate_json(record.model_dump_json()) == record
    data["provenance"]["first_acquisition"]["body_metadata"][field] += 1
    if field == "decoded_bytes":
        data["response"]["byte_count"] += 1
    with pytest.raises(ValidationError, match="RSS"):
        EVIDENCE.validate_python(data)
    for deep in (False, True):
        with pytest.raises(ValidationError, match="RSS"):
            record.model_copy(
                update={"provenance": data["provenance"], "response": data["response"]}, deep=deep
            )


def test_catalog_and_publication_specific_boundaries(examples):
    for value in [1, 10000]:
        assert (
            CatalogContext.model_validate(examples["catalog"]["catalog"] | {"count": value}).count
            == value
        )
    for value in [0, 10001, True, "1", 1.0]:
        with pytest.raises(ValidationError):
            CatalogContext.model_validate(examples["catalog"]["catalog"] | {"count": value})
    fields = examples["catalog"]["fields"] | {"notes": "é" * 8192, "cwes": ["synthetic"] * 128}
    CatalogFields.model_validate(fields)
    for update in [{"notes": "x" * 8193}, {"notes": b"bytes"}, {"cwes": ["synthetic"] * 129}]:
        with pytest.raises(ValidationError):
            CatalogFields.model_validate(fields | update)
    raw = {"precision": "unknown", "parse_outcome": "invalid", "supplied_text": "x" * 8192}
    PublicationDate.model_validate(raw)
    with pytest.raises(ValidationError):
        PublicationDate.model_validate(raw | {"supplied_text": "x" * 8193})


def test_reference_validation_has_no_dns_or_clock_side_effects(examples, monkeypatch):
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("No DNS access in contracts")

    monkeypatch.setattr(socket, "getaddrinfo", denied)
    record = EVIDENCE.validate_python(examples["microsoft"])
    assert (
        record.model_dump_json()
        == EVIDENCE.validate_python(examples["microsoft"]).model_dump_json()
    )
    with pytest.raises(AssertionError, match="Network access is forbidden"):
        socket.create_connection(("example.org", 443))


def test_nested_schema_versions_and_caller_supplied_markings(examples):
    for path in [
        "original.schema_version",
        "original.parent.schema_version",
        "sanitized.transformation.schema_version",
        "provenance.schema_version",
        "provenance.policy.schema_version",
    ]:
        with pytest.raises(ValidationError):
            EVIDENCE.validate_python(replace(examples["microsoft"], path, "2.0"))
    for key in ("evidence_id", "logical_item_id"):
        data = copy.deepcopy(examples["microsoft"])
        del data[key]
        with pytest.raises(ValidationError):
            EVIDENCE.validate_python(data)
    explicit = EVIDENCE.validate_python(examples["microsoft"] | {"tlp": "TLP:RED"})
    assert explicit.tlp.value == "TLP:RED"


@pytest.mark.parametrize("text", ["", " \t\n"])
def test_parsed_date_requires_nonblank_source_text(text):
    with pytest.raises(ValidationError):
        PublicationDate.model_validate(
            {
                "precision": "date",
                "parse_outcome": "parsed",
                "supplied_text": text,
                "date": "2026-01-15",
            }
        )


@pytest.mark.parametrize("field", ["date", "timestamp"])
def test_publication_precision_rejects_other_parsed_value(field):
    values = {"date": "2026-01-15", "timestamp": "2026-01-15T00:00:00Z"}
    other = "timestamp" if field == "date" else "date"
    with pytest.raises(ValidationError):
        PublicationDate.model_validate(
            {
                "precision": field,
                "parse_outcome": "parsed",
                "supplied_text": "synthetic date",
                field: values[field],
                other: values[other],
            }
        )


def test_metadata_digest_is_separate_from_artifact_domain(examples):
    for data, model, field in [
        (examples["microsoft"], FeedFullTextEvidenceRevision, "metadata_digest"),
        (examples["manifest"]["items"][0], FeedManifestItem, "evidence_digest"),
    ]:
        with pytest.raises(ValidationError):
            model.model_validate(
                data | {field: {"sha256": "a" * 64, "domain": "feed-field-html-utf8-v1"}}
            )
