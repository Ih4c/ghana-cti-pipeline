"""Golden vectors and identity invariants; all source material is synthetic."""

import copy
import json
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import TypeAdapter

from ghana_cti_pipeline.core.digests import compute_digest
from ghana_cti_pipeline.core.evidence import EvidenceRevisionV2
from ghana_cti_pipeline.core.identities import (
    IDENTITY_PROFILE,
    artifact_association_id,
    derived_representation_id,
    evidence_association_id,
    evidence_metadata_digest,
    logical_item_id,
    processing_manifest_digest,
    processing_manifest_id,
    retrieval_observation_id,
    source_revision_id,
    source_revision_projection,
    validate_evidence_identities,
    validate_manifest_evidence,
)
from ghana_cti_pipeline.core.processing import ProcessingManifest
from ghana_cti_pipeline.core.retrieval import EvidenceObservation

FIXTURES = Path(__file__).parent / "fixtures"
VECTORS = json.loads((FIXTURES / "identity_vectors.json").read_text("utf-8"))
EVIDENCE = TypeAdapter(EvidenceRevisionV2)


@pytest.fixture
def examples():
    return json.loads((FIXTURES / "evidence_v2.json").read_text("utf-8"))


def prepared(examples, base="microsoft", change=None):
    data = copy.deepcopy(examples[base])
    change = change or {}

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in change and key in ("source_id", "policy_version", "retrieval_id"):
                    node[key] = change[key]
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    data["provenance"]["identity_profile"] = IDENTITY_PROFILE
    for key in ("source_key", "publication"):
        if key in change:
            data["provenance"][key] = change[key]
    if "title" in change:
        data["title"] = change["title"]
    if data["mode"] == "feed_full_text":
        for key, domain, child in [
            ("original", "feed-field-html-utf8-v1", "sanitized"),
            ("sanitized", "sanitized-html-utf8-v1", "plain_text"),
            ("plain_text", "plain-text-utf8-v1", None),
        ]:
            text = change.get(
                key + "_text",
                {
                    "original": "<p>Alpha café</p>\r\n",
                    "sanitized": "<p>Alpha café</p>",
                    "plain_text": "Alpha café",
                }[key],
            )
            digest = compute_digest(domain, text)
            data[key].update(sha256=digest.sha256, byte_count=len(text.encode("utf-8")))
            if child:
                data[child]["parent"]["sha256"] = digest.sha256
        for key, setting in [
            ("sanitized", "sanitizer_version"),
            ("plain_text", "extractor_version"),
        ]:
            if setting in change:
                data[key]["transformation"]["implementation_version"] = change[setting]
    return EVIDENCE.validate_python(data)


def bind(record):
    """Explicit validated copies, never a mutation or persistence operation."""
    keys = (
        ["response", "original", "sanitized", "plain_text"]
        if record.mode == "feed_full_text"
        else ["response", "entry"]
    )
    artifacts = {}
    previous = None
    for key in keys:
        artifact = getattr(record, key)
        if previous is not None:
            artifact = artifact.model_copy(
                update={
                    "parent": artifact.parent.model_copy(
                        update={"artifact_id": previous.artifact_id}
                    )
                }
            )
        artifact = artifact.model_copy(update={"artifact_id": artifact_association_id(artifact)})
        artifacts[key] = artifact
        previous = artifact
    record = record.model_copy(
        update=artifacts
        | {
            "logical_item_id": logical_item_id(
                record.provenance.source_id, record.provenance.source_key
            ),
            "evidence_id": source_revision_id(record),
        }
    )
    return record.model_copy(update={"metadata_digest": evidence_metadata_digest(record)})


def linked_records(examples, record):
    data = json.loads((FIXTURES / "retrieval.json").read_text("utf-8"))["observation"]
    p = record.provenance
    data.update(
        retrieval_id=p.first_acquisition.retrieval_id,
        evidence_id=record.evidence_id,
        evidence_kind="hybrid",
        evidence_schema_version="2.0",
        locator=p.locator,
        adapter_version=p.adapter_version,
        source_policy_id=p.policy.policy_id,
        source_policy_version=p.policy.policy_version,
    )
    observation = EvidenceObservation.model_validate(data)
    manifest = copy.deepcopy(examples["manifest"])
    chain = (
        [record.original, record.sanitized, record.plain_text]
        if record.mode == "feed_full_text"
        else [record.entry]
    )
    manifest.update(
        mode=record.mode,
        policy=p.policy,
        retrieval=p.first_acquisition,
        request_variant_id=p.request_variant_id,
        adapter_version=p.adapter_version,
        parser_version=p.parser_version,
        response=record.response,
        artifacts=chain,
    )
    item = {
        "mode": record.mode,
        "evidence_id": record.evidence_id,
        "evidence_kind": "hybrid",
        "evidence_schema_version": "2.0",
        "evidence_digest": record.metadata_digest,
        "locator": p.locator,
    }
    if record.mode == "feed_full_text":
        item.update(
            original_id=record.original.artifact_id,
            sanitized_id=record.sanitized.artifact_id,
            plain_text_id=record.plain_text.artifact_id,
        )
    else:
        item["entry_id"] = record.entry.artifact_id
    manifest["items"] = [item]
    model = ProcessingManifest.model_validate(manifest)
    model = model.model_copy(update={"digest": processing_manifest_digest(model)})
    return observation, model


@pytest.mark.parametrize("vector", VECTORS["identities"], ids=lambda v: v["name"])
def test_fixed_identity_and_association_vectors(examples, vector):
    from ghana_cti_pipeline.core.digests import canonical_json

    record = prepared(examples, vector["base"], vector["change"])
    expected = vector["expected"]
    original = record.model_dump_json()
    assert (
        str(logical_item_id(record.provenance.source_id, record.provenance.source_key))
        == expected["logical_item_id"]
    )
    assert str(source_revision_id(record)) == expected["source_revision_id"]
    assert (
        canonical_json(source_revision_projection(record)).hex()
        == expected["source_projection_utf8_hex"]
    )
    if record.mode == "feed_full_text":
        assert str(derived_representation_id(record, "sanitized_html")) == expected["sanitized_id"]
        assert str(derived_representation_id(record, "plain_text")) == expected["plain_text_id"]
    bound = bind(record)
    assert record.model_dump_json() == original
    keys = (
        ["response", "original", "sanitized", "plain_text"]
        if record.mode == "feed_full_text"
        else ["response", "entry"]
    )
    for key in keys:
        assert str(getattr(bound, key).artifact_id) == expected[key + "_association_id"]
    assert bound.metadata_digest.sha256 == expected["metadata_sha256"]
    assert str(evidence_association_id(bound)) == expected["evidence_association_id"]
    observation, manifest = linked_records(examples, bound)
    assert str(retrieval_observation_id(observation)) == expected["observation_id"]
    assert manifest.digest.sha256 == expected["manifest_sha256"]
    assert str(processing_manifest_id(manifest)) == expected["manifest_id"]
    assert bind(record) == bind(record)


def test_a_b_a_reuses_revision_but_not_acquisition_or_observation(examples):
    a = bind(prepared(examples))
    b = bind(prepared(examples, change={"original_text": "<p>B</p>"}))
    again = bind(
        prepared(examples, change={"retrieval_id": "00000000-0000-4000-8000-000000009999"})
    )
    assert a.evidence_id == again.evidence_id != b.evidence_id
    assert a.logical_item_id == b.logical_item_id == again.logical_item_id
    assert evidence_association_id(a) != evidence_association_id(again)
    obs1, _ = linked_records(examples, a)
    obs2, _ = linked_records(examples, again)
    assert retrieval_observation_id(obs1) != retrieval_observation_id(obs2)
    assert retrieval_observation_id(obs1) == retrieval_observation_id(obs1)


def test_transform_changes_preserve_revision_and_propagate_to_children(examples):
    a = prepared(examples)
    sanitized = prepared(examples, change={"sanitizer_version": "synthetic-2"})
    extracted = prepared(examples, change={"extractor_version": "synthetic-2"})
    assert source_revision_id(a) == source_revision_id(sanitized) == source_revision_id(extracted)
    assert derived_representation_id(a, "sanitized_html") != derived_representation_id(
        sanitized, "sanitized_html"
    )
    assert derived_representation_id(a, "plain_text") != derived_representation_id(
        sanitized, "plain_text"
    )
    assert derived_representation_id(a, "sanitized_html") == derived_representation_id(
        extracted, "sanitized_html"
    )
    assert derived_representation_id(a, "plain_text") != derived_representation_id(
        extracted, "plain_text"
    )
    assert evidence_association_id(bind(a)) != evidence_association_id(bind(sanitized))


def test_identical_derived_bytes_different_original_parent(examples):
    a = prepared(examples)
    b = prepared(examples, change={"original_text": "<p>Different original</p>"})
    assert a.sanitized.sha256 == b.sanitized.sha256
    assert a.plain_text.sha256 == b.plain_text.sha256
    assert derived_representation_id(a, "sanitized_html") != derived_representation_id(
        b, "sanitized_html"
    )
    assert derived_representation_id(a, "plain_text") != derived_representation_id(b, "plain_text")


def test_source_key_boundaries_and_no_fuzzy_matching():
    url = "https://example.org/a?b=2&a=%2f#ref"
    native = {"kind": "native_id", "value": url}
    fallback = {"kind": "original_url", "value": url}
    assert logical_item_id("source", native) != logical_item_id("source", fallback)
    assert logical_item_id("source", native) != logical_item_id("other", native)
    assert logical_item_id("source", native) != logical_item_id(
        "source", native | {"value": url + " "}
    )
    for invalid in ["", " " * 256, "s" * 257, 1, b"source"]:
        with pytest.raises(ValueError):
            logical_item_id(invalid, native)
    logical_item_id("s" * 256, {"kind": "native_id", "value": "n" * 8192})
    for invalid in ["", "x" * 8193, 1, b"key"]:
        with pytest.raises(ValueError):
            logical_item_id("source", {"kind": "native_id", "value": invalid})
    for invalid in [
        {"kind": "unknown", "value": "x"},
        {"kind": "original_url", "value": "javascript:x"},
    ]:
        with pytest.raises(ValueError):
            logical_item_id("source", invalid)


def test_non_source_metadata_does_not_change_revision(examples):
    a = prepared(examples, "catalog")
    b = a.model_copy(
        update={
            "catalog": a.catalog.model_copy(update={"catalog_version": "different", "count": 999})
        }
    )
    p = a.provenance.model_copy(
        update={
            "adapter_version": "other",
            "parser_version": "other",
            "publisher": "Renamed configuration",
        }
    )
    c = a.model_copy(update={"provenance": p})
    assert source_revision_id(a) == source_revision_id(b) == source_revision_id(c)
    a = prepared(examples)
    policy = prepared(examples, change={"policy_version": "renewed"})
    assert source_revision_id(a) == source_revision_id(policy)
    assert evidence_association_id(bind(a)) != evidence_association_id(bind(policy))


def test_source_fields_and_original_url_are_revision_inputs(examples):
    a = prepared(examples)
    for p in [
        a.provenance.model_copy(update={"original_url": "https://example.org/changed"}),
        a.provenance.model_copy(update={"publisher_origin": "supplied"}),
        a.provenance.model_copy(
            update={
                "publication": {
                    "precision": "date",
                    "parse_outcome": "parsed",
                    "supplied_text": "2026-01-15",
                    "date": "2026-01-15",
                }
            }
        ),
    ]:
        assert source_revision_id(a) != source_revision_id(a.model_copy(update={"provenance": p}))


def test_digest_and_id_self_fields_are_excluded(examples):
    a = bind(prepared(examples))
    wrong = a.model_copy(
        update={"metadata_digest": a.metadata_digest.model_copy(update={"sha256": "0" * 64})}
    )
    assert evidence_metadata_digest(a) == evidence_metadata_digest(wrong)
    with pytest.raises(ValueError):
        evidence_association_id(wrong)
    _, manifest = linked_records(examples, a)
    changed = manifest.model_copy(
        update={
            "manifest_id": UUID(int=999),
            "digest": manifest.digest.model_copy(update={"sha256": "0" * 64}),
        }
    )
    assert processing_manifest_digest(manifest) == processing_manifest_digest(changed)
    with pytest.raises(ValueError):
        processing_manifest_id(changed)
    with pytest.raises(ValueError):
        evidence_metadata_digest(prepared(examples))


def test_unsupported_profiles_and_representation_kinds(examples):
    a = bind(prepared(examples))
    obs, manifest = linked_records(examples, a)
    manifest = complete_manifest(manifest)
    calls = [
        lambda p: logical_item_id(a.provenance.source_id, a.provenance.source_key, profile=p),
        lambda p: source_revision_id(a, profile=p),
        lambda p: source_revision_projection(a, profile=p),
        lambda p: derived_representation_id(a, "plain_text", profile=p),
        lambda p: artifact_association_id(a.original, profile=p),
        lambda p: evidence_metadata_digest(a, profile=p),
        lambda p: evidence_association_id(a, profile=p),
        lambda p: processing_manifest_digest(manifest, profile=p),
        lambda p: processing_manifest_id(manifest, profile=p),
        lambda p: retrieval_observation_id(obs, profile=p),
        lambda p: validate_evidence_identities(a, profile=p),
        lambda p: validate_manifest_evidence(manifest, (a,), profile=p),
    ]
    for profile in ["unknown", "", None, 1]:
        for call in calls:
            with pytest.raises(ValueError):
                call(profile)
    with pytest.raises(ValueError):
        source_revision_id(EVIDENCE.validate_python(examples["microsoft"]))
    for kind in ["original_html", "catalog_entry", "unknown", None]:
        with pytest.raises(ValueError):
            derived_representation_id(a, kind)
    with pytest.raises(ValueError):
        derived_representation_id(prepared(examples, "catalog"), "plain_text")


def test_no_filesystem_network_clock_or_randomness_during_helpers(examples, monkeypatch):
    import builtins
    import io
    import os
    import socket
    import time
    import uuid

    a = bind(prepared(examples))
    obs, manifest = linked_records(examples, a)
    manifest = complete_manifest(manifest)
    expected = evidence_association_id(a)

    def denied(*args, **kwargs):
        raise AssertionError(
            "Identity helpers must perform no I/O or generation of time/randomness"
        )

    with monkeypatch.context() as guard:
        for obj, name in [
            (builtins, "open"),
            (io, "open"),
            (os, "open"),
            (socket, "getaddrinfo"),
            (socket, "create_connection"),
            (socket.socket, "connect"),
            (time, "time"),
            (uuid, "uuid4"),
            (os, "urandom"),
        ]:
            guard.setattr(obj, name, denied)
        assert evidence_association_id(a) == expected
        source_revision_id(a)
        derived_representation_id(a, "plain_text")
        artifact_association_id(a.original)
        processing_manifest_digest(manifest)
        processing_manifest_id(manifest)
        retrieval_observation_id(obs)
        validate_evidence_identities(a)
        validate_manifest_evidence(manifest, (a,))
        assert compute_digest("plain-text-utf8-v1", "synthetic").sha256


def test_catalog_projection_changes_only_association_original_digest_changes_revision(examples):
    original = prepared(examples, "catalog")
    changed = original.model_copy(
        update={
            "fields": original.fields.model_copy(update={"requiredAction": "Corrected mapping"})
        }
    )
    assert source_revision_id(original) == source_revision_id(changed)
    assert evidence_association_id(bind(original)) != evidence_association_id(bind(changed))
    extension = original.model_copy(
        update={"entry": original.entry.model_copy(update={"sha256": "0" * 64})}
    )
    assert source_revision_id(original) != source_revision_id(extension)
    assert original.evidence_id == changed.evidence_id  # Helpers do not silently rewrite records.


def test_publication_interpretation_does_not_change_original_revision(examples):
    original = prepared(
        examples,
        change={
            "publication": {
                "precision": "date",
                "parse_outcome": "parsed",
                "supplied_text": "2026-01-15",
                "date": "2026-01-15",
            }
        },
    )
    publication = original.provenance.publication.model_copy(
        update={"precision": "unknown", "parse_outcome": "invalid", "date": None, "timestamp": None}
    )
    changed = original.model_copy(
        update={"provenance": original.provenance.model_copy(update={"publication": publication})}
    )
    assert source_revision_id(original) == source_revision_id(changed)
    assert evidence_association_id(bind(original)) != evidence_association_id(bind(changed))


def complete_manifest(manifest):
    manifest = manifest.model_copy(update={"digest": processing_manifest_digest(manifest)})
    return manifest.model_copy(update={"manifest_id": processing_manifest_id(manifest)})


@pytest.mark.parametrize("base", ["catalog", "microsoft", "google"])
def test_supplied_cross_record_identity_links(examples, base):
    record = bind(prepared(examples, base))
    _, manifest = linked_records(examples, record)
    manifest = complete_manifest(manifest)
    validate_evidence_identities(record)
    validate_manifest_evidence(manifest, (record,))
    with pytest.raises(ValueError, match="duplicate"):
        validate_manifest_evidence(manifest, (record, record))
    with pytest.raises(ValueError, match="does not match"):
        validate_manifest_evidence(manifest, ())
    with pytest.raises(ValueError, match="tuple"):
        validate_manifest_evidence(manifest, [record])
    with pytest.raises(ValueError, match="manifest ID"):
        validate_manifest_evidence(
            manifest.model_copy(update={"manifest_id": UUID(int=999)}), (record,)
        )


@pytest.mark.parametrize("field", ["request_variant_id", "adapter_version", "parser_version"])
def test_manifest_rejects_cross_record_processing_context(examples, field):
    record = bind(prepared(examples))
    _, manifest = linked_records(examples, record)
    changed = complete_manifest(manifest.model_copy(update={field: "other"}))
    with pytest.raises(ValueError, match="provenance/identity"):
        validate_manifest_evidence(changed, (record,))


def test_reprocessed_bundle_cannot_replace_an_existing_manifest_association(examples):
    original = bind(prepared(examples))
    changed = bind(prepared(examples, change={"sanitizer_version": "different"}))
    _, manifest = linked_records(examples, original)
    manifest = complete_manifest(manifest)
    assert original.evidence_id == changed.evidence_id
    with pytest.raises(ValueError, match="provenance/identity"):
        validate_manifest_evidence(manifest, (changed,))
    changed_item = manifest.items[0].model_copy(update={"evidence_digest": changed.metadata_digest})
    changed_manifest = complete_manifest(manifest.model_copy(update={"items": (changed_item,)}))
    with pytest.raises(ValueError, match="artifact associations"):
        validate_manifest_evidence(changed_manifest, (changed,))
    validate_manifest_evidence(manifest, (original,))


def test_arbitrary_artifact_ids_and_incomplete_manifest_references(examples):
    original = prepared(examples)
    with pytest.raises(ValueError, match="artifact association ID"):
        validate_evidence_identities(original)
    record = bind(original)
    _, manifest = linked_records(examples, record)
    manifest = complete_manifest(
        manifest.model_copy(update={"completeness": "incomplete", "expected_item_count": 2})
    )
    validate_manifest_evidence(manifest, (record,))
    with pytest.raises(ValueError, match="does not match"):
        validate_manifest_evidence(manifest, ())


def test_native_ids_do_not_merge_identical_url_title_or_content(examples):
    original = prepared(examples)
    other = prepared(examples, change={"source_key": {"kind": "native_id", "value": "other-guid"}})
    assert original.original.sha256 == other.original.sha256
    assert original.title == other.title
    assert original.provenance.original_url == other.provenance.original_url
    assert source_revision_id(original) != source_revision_id(other)


def test_observation_self_id_and_artifact_self_id_do_not_change_identity(examples):
    record = bind(prepared(examples))
    observation, _ = linked_records(examples, record)
    assert retrieval_observation_id(observation) == retrieval_observation_id(
        observation.model_copy(update={"observation_id": UUID(int=999)})
    )
    assert artifact_association_id(record.original) == artifact_association_id(
        record.original.model_copy(update={"artifact_id": UUID(int=999)})
    )


def test_manifest_order_and_processing_version_change_only_manifest_association(examples):
    record = bind(prepared(examples))
    _, manifest = linked_records(examples, record)
    changed = manifest.model_copy(update={"artifacts": tuple(reversed(manifest.artifacts))})
    assert processing_manifest_digest(manifest) != processing_manifest_digest(changed)
    changed = manifest.model_copy(update={"parser_version": "different-parser"})
    assert processing_manifest_digest(manifest) != processing_manifest_digest(changed)
    assert record.evidence_id == source_revision_id(record)
