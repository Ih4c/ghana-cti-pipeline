"""Policy, lifecycle and batch assertions remain offline metadata validation."""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ghana_cti_pipeline.core.artifacts import ArtifactAvailability
from ghana_cti_pipeline.core.processing import ProcessingManifest
from ghana_cti_pipeline.core.source_policy import SourcePolicy


@pytest.fixture
def examples():
    return json.loads((Path(__file__).parent / "fixtures/evidence_v2.json").read_text("utf-8"))


def uid(n):
    return f"00000000-0000-4000-8000-{n:012d}"


def batch(examples, mode, count):
    """Distinct caller-supplied synthetic IDs, not a source identity algorithm."""
    result = copy.deepcopy(examples["manifest"])
    result.update(mode=mode, expected_item_count=count, items=[], artifacts=[])
    if mode == "catalog_entry":
        catalog = examples["catalog"]
        result["policy"] = copy.deepcopy(catalog["provenance"]["policy"])
        result["retrieval"] = copy.deepcopy(catalog["provenance"]["first_acquisition"])
        result["response"] = copy.deepcopy(catalog["response"])
    for i in range(count):
        locator = f"/items/{i}"
        if mode == "catalog_entry":
            artifact = copy.deepcopy(examples["catalog"]["entry"])
            artifact.update(artifact_id=uid(1000 + i), locator=locator)
            result["artifacts"].append(artifact)
            item = {"entry_id": artifact["artifact_id"]}
        else:
            original, sanitized, plain = copy.deepcopy(examples["manifest"]["artifacts"])
            original.update(artifact_id=uid(1000 + i * 3), locator=locator)
            sanitized["artifact_id"] = uid(1001 + i * 3)
            plain["artifact_id"] = uid(1002 + i * 3)
            sanitized["parent"]["artifact_id"] = original["artifact_id"]
            plain["parent"]["artifact_id"] = sanitized["artifact_id"]
            result["artifacts"].extend((original, sanitized, plain))
            item = {
                "original_id": original["artifact_id"],
                "sanitized_id": sanitized["artifact_id"],
                "plain_text_id": plain["artifact_id"],
            }
        result["items"].append(
            item
            | {
                "mode": mode,
                "evidence_id": uid(100000 + i),
                "evidence_kind": "hybrid",
                "evidence_schema_version": "2.0",
                "evidence_digest": examples["microsoft"]["metadata_digest"],
                "locator": locator,
            }
        )
    return result


@pytest.mark.parametrize("mode", ["catalog_entry", "feed_full_text"])
def test_complete_and_incomplete_batches(examples, mode):
    data = batch(examples, mode, 2)
    value = ProcessingManifest.model_validate(data)
    assert ProcessingManifest.model_validate_json(value.model_dump_json()) == value
    with pytest.raises(ValidationError):
        ProcessingManifest.model_validate(data | {"expected_item_count": 3})
    assert (
        ProcessingManifest.model_validate(
            data | {"completeness": "incomplete", "expected_item_count": 3}
        ).completeness
        == "incomplete"
    )
    assert ProcessingManifest.model_validate(batch(examples, mode, 0)).items == ()


@pytest.mark.parametrize("field", ["original_id", "sanitized_id", "plain_text_id"])
def test_manifest_item_requires_full_text_associations(examples, field):
    data = examples["manifest"]
    del data["items"][0][field]
    with pytest.raises(ValidationError):
        ProcessingManifest.model_validate(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_artifact",
        "duplicate_artifact",
        "orphan_artifact",
        "wrong_parent",
        "wrong_locator",
        "wrong_policy",
        "wrong_mode",
        "duplicate_item",
        "wrong_digest_domain",
        "wrong_response",
        "wrong_evidence_version",
        "wrong_source",
        "unknown_field",
        "missing_digest",
    ],
)
def test_manifest_contradictions_reject(examples, mutation):
    data = examples["manifest"]
    if mutation == "missing_artifact":
        data["artifacts"].pop()
    elif mutation == "duplicate_artifact":
        data["artifacts"].append(data["artifacts"][0])
    elif mutation == "orphan_artifact":
        orphan = copy.deepcopy(data["artifacts"][0])
        orphan["artifact_id"] = uid(999)
        data["artifacts"].append(orphan)
    elif mutation == "wrong_parent":
        data["artifacts"][1]["parent"]["sha256"] = "0" * 64
    elif mutation == "wrong_locator":
        data["items"][0]["locator"] = "/wrong"
    elif mutation == "wrong_policy":
        data["artifacts"][0]["policy"]["policy_version"] = "other"
    elif mutation == "wrong_mode":
        data["mode"] = "catalog_entry"
    elif mutation == "duplicate_item":
        data["items"].append(copy.deepcopy(data["items"][0]))
        data["expected_item_count"] = 2
    elif mutation == "wrong_digest_domain":
        data["digest"]["domain"] = "decoded-http-entity-v1"
    elif mutation == "wrong_response":
        data["response"]["byte_count"] = 99
    elif mutation == "wrong_evidence_version":
        data["items"][0]["evidence_schema_version"] = "1.0"
    elif mutation == "wrong_source":
        data["policy"]["source_id"] = "other"
    elif mutation == "unknown_field":
        data["checkpoint_eligible"] = True
    elif mutation == "missing_digest":
        del data["digest"]
    with pytest.raises(ValidationError):
        ProcessingManifest.model_validate(data)


@pytest.mark.parametrize("kind", ["original_html", "sanitized_html", "plain_text", "catalog_entry"])
def test_aggregate_byte_limit_exact_and_above(examples, kind):
    mode = "catalog_entry" if kind == "catalog_entry" else "feed_full_text"
    data = batch(examples, mode, 3)
    cap = 8 * 1024 * 1024 if mode == "catalog_entry" else 2 * 1024 * 1024
    matching = [a for a in data["artifacts"] if a["kind"] == kind]
    matching[0]["byte_count"] = cap // 2
    matching[1]["byte_count"] = cap // 2 - 1
    matching[2]["byte_count"] = 1
    ProcessingManifest.model_validate(data)
    matching[2]["byte_count"] = 2
    with pytest.raises(ValidationError, match="aggregate"):
        ProcessingManifest.model_validate(data)


@pytest.mark.parametrize("mode,cap", [("catalog_entry", 10000), ("feed_full_text", 500)])
def test_item_count_exact_and_above(examples, mode, cap):
    data = batch(examples, mode, cap)
    ProcessingManifest.model_validate(data)
    # Larger declared counts reject before a later parser can manufacture completeness.
    with pytest.raises(ValidationError):
        ProcessingManifest.model_validate(
            data | {"expected_item_count": cap + 1, "completeness": "incomplete"}
        )
    data["items"].append(copy.deepcopy(data["items"][-1]))
    with pytest.raises(ValidationError):
        ProcessingManifest.model_validate(data)


@pytest.mark.parametrize("value", [-1, True, 1.0, "1", 10001])
def test_manifest_count_strictness(examples, value):
    with pytest.raises(ValidationError):
        ProcessingManifest.model_validate(examples["manifest"] | {"expected_item_count": value})


@pytest.mark.parametrize("field", ["decoded_bytes", "transferred_bytes"])
def test_rss_response_cap_in_manifest(examples, field):
    data = examples["manifest"]
    data["retrieval"]["body_metadata"][field] = 2 * 1024 * 1024
    if field == "decoded_bytes":
        data["response"]["byte_count"] = 2 * 1024 * 1024
    ProcessingManifest.model_validate(data)
    data["retrieval"]["body_metadata"][field] += 1
    if field == "decoded_bytes":
        data["response"]["byte_count"] += 1
    with pytest.raises(ValidationError, match="RSS"):
        ProcessingManifest.model_validate(data)


@pytest.mark.parametrize("state", ["available", "expired", "deleted", "unavailable"])
def test_separate_availability_records(examples, state):
    data = examples["availability"] | {"state": state}
    if state == "expired":
        data["recorded_at"] = data["retention_until"]
    record = ArtifactAvailability.model_validate(data)
    assert record.state == state
    assert "state" not in examples["microsoft"]["original"]


def test_availability_expiration_and_copy_validation(examples):
    data = examples["availability"]
    for update in [
        {"state": "expired"},
        {"recorded_at": data["retention_until"]},
        {"state": "present"},
    ]:
        with pytest.raises(ValidationError):
            ArtifactAvailability.model_validate(data | update)
    record = ArtifactAvailability.model_validate(data)
    for deep in (False, True):
        with pytest.raises(ValidationError):
            record.model_copy(update={"state": "expired"}, deep=deep)


def test_policy_id_is_not_verified_permission(examples):
    policy = SourcePolicy.model_validate(examples["policy"])
    assert policy.basis_status == "unresolved"
    assert policy.permitted_processing == ()
    with pytest.raises(ValidationError):
        SourcePolicy.model_validate(examples["policy"] | {"basis_status": "documented"})
    documented = SourcePolicy.model_validate(
        examples["policy"]
        | {
            "basis_status": "documented",
            "basis_references": ["https://example.org/synthetic-terms"],
            "reviewed_at": "2026-01-01T00:00:00Z",
            "permitted_artifacts": [
                "http_response",
                "original_html",
                "sanitized_html",
                "plain_text",
            ],
            "permitted_processing": [
                "retrieve",
                "retain",
                "sanitize_html",
                "extract_text",
                "internal_use",
                "backup",
            ],
        }
    )
    assert "permission_verified" not in documented.model_dump()
    assert SourcePolicy.model_validate_json(documented.model_dump_json()) == documented


@pytest.mark.parametrize(
    "update",
    [
        {"expires_at": "2026-01-01T00:00:00Z"},
        {"expires_at": "2025-01-01T00:00:00Z"},
        {"permitted_artifacts": ["catalog_entry"]},
        {"permitted_processing": ["publish"]},
        {"permitted_processing": ["retain", "retain"]},
        {"permitted_artifacts": ["http_response", "http_response"]},
        {"basis_status": "approved"},
        {"basis_references": ["https://example.org/"] * 2},
    ],
)
def test_policy_contradictions_and_copy_updates(examples, update):
    with pytest.raises(ValidationError):
        SourcePolicy.model_validate(examples["policy"] | update)
    record = SourcePolicy.model_validate(examples["policy"])
    for deep in (False, True):
        with pytest.raises(ValidationError):
            record.model_copy(update=update, deep=deep)


@pytest.mark.parametrize(
    "field", ["response", "original", "derived", "metadata", "digests", "audit", "backups"]
)
def test_retention_requires_explicit_valid_deadline_per_class(examples, field):
    data = examples["policy"]
    for bad in ["2025-01-01T00:00:00Z", "2026-02-01", 1, None]:
        with pytest.raises(ValidationError):
            SourcePolicy.model_validate(data | {"retention": data["retention"] | {field: bad}})
    del data["retention"][field]
    with pytest.raises(ValidationError):
        SourcePolicy.model_validate(data)


def test_policy_reference_count_boundary(examples):
    refs = [f"https://example.org/terms/{i}" for i in range(32)]
    SourcePolicy.model_validate(examples["policy"] | {"basis_references": refs})
    with pytest.raises(ValidationError):
        SourcePolicy.model_validate(
            examples["policy"] | {"basis_references": refs + ["https://example.org/extra"]}
        )
