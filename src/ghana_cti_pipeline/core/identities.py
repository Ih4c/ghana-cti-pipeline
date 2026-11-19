"""Deterministic identities and explicit projections; no mutation or state lookup."""

from uuid import UUID, uuid5

from pydantic import TypeAdapter

from ghana_cti_pipeline.core.artifacts import ArtifactReference
from ghana_cti_pipeline.core.digests import canonical_json, compute_digest
from ghana_cti_pipeline.core.evidence import (
    CatalogEvidenceRevision,
    EvidenceMetadataDigest,
    EvidenceRevisionV2,
    FeedFullTextEvidenceRevision,
    SourceKey,
)
from ghana_cti_pipeline.core.evidence_values import Identifier
from ghana_cti_pipeline.core.processing import ManifestDigest, ProcessingManifest
from ghana_cti_pipeline.core.retrieval import EvidenceObservation

IDENTITY_PROFILE = "cti-identity-v1"
LOGICAL_NAMESPACE = UUID("c9dd1d2a-e8b2-5fba-b58b-100562599777")
REVISION_NAMESPACE = UUID("f4798c76-659b-5f49-81a8-fb47a85ca766")
DERIVED_NAMESPACE = UUID("5b9b8f86-4d66-55f2-8845-124e0ee93ff2")
ARTIFACT_NAMESPACE = UUID("c4be50e4-6b83-54d9-bda5-9c36c8ef5536")
ASSOCIATION_NAMESPACE = UUID("fa9ff4b2-257d-5d99-b309-e202770d59b0")
MANIFEST_NAMESPACE = UUID("b69acd17-2d88-5151-9f49-09eb68cbb0f4")
OBSERVATION_NAMESPACE = UUID("a4ab0ac4-f3a5-5177-a262-2bb9df3ff261")
_evidence = TypeAdapter(EvidenceRevisionV2)
_artifact = TypeAdapter(ArtifactReference)
_source_key = TypeAdapter(SourceKey)
_identifier = TypeAdapter(Identifier)


def _check_profile(profile: str) -> None:
    if type(profile) is not str or profile != IDENTITY_PROFILE:
        raise ValueError("unsupported identity profile")


def _id(namespace: UUID, projection: object, profile: str) -> UUID:
    _check_profile(profile)
    name = canonical_json({"profile": profile, "projection": projection}).decode("utf-8")
    return uuid5(namespace, name)


def _record(evidence: EvidenceRevisionV2, profile: str):
    _check_profile(profile)
    record = _evidence.validate_python(evidence)
    if record.provenance.identity_profile != profile:
        raise ValueError("evidence identity profile must match the selected profile")
    return record


def logical_item_id(
    source_id: str, source_key: SourceKey, *, profile: str = IDENTITY_PROFILE
) -> UUID:
    _check_profile(profile)
    source_id = _identifier.validate_python(source_id)
    key = _source_key.validate_python(source_key)
    return _id(
        LOGICAL_NAMESPACE,
        {"source_id": source_id, "key": {"kind": key.kind, "value": key.value}},
        profile,
    )


def source_revision_projection(
    evidence: EvidenceRevisionV2, *, profile: str = IDENTITY_PROFILE
) -> dict:
    record = _record(evidence, profile)
    provenance = record.provenance
    original = record.entry if isinstance(record, CatalogEvidenceRevision) else record.original
    source = {
        "original_url": provenance.original_url,
        "publication": provenance.publication.model_dump(mode="json"),
        "publisher": provenance.publisher if provenance.publisher_origin == "supplied" else None,
        "byline": provenance.byline if provenance.byline_origin == "supplied" else None,
    }
    if isinstance(record, CatalogEvidenceRevision):
        source["fields"] = record.fields.model_dump(mode="json")
    else:
        source["title"] = record.title
    return {
        "logical_item_id": str(
            logical_item_id(provenance.source_id, provenance.source_key, profile=profile)
        ),
        "mode": record.mode,
        "original": {"domain": original.digest_domain, "sha256": original.sha256},
        "source": source,
    }


def source_revision_id(evidence: EvidenceRevisionV2, *, profile: str = IDENTITY_PROFILE) -> UUID:
    return _id(REVISION_NAMESPACE, source_revision_projection(evidence, profile=profile), profile)


def derived_representation_id(
    evidence: EvidenceRevisionV2,
    kind: str,
    *,
    profile: str = IDENTITY_PROFILE,
) -> UUID:
    record = _record(evidence, profile)
    if (
        type(kind) is not str
        or not isinstance(record, FeedFullTextEvidenceRevision)
        or kind
        not in {
            "sanitized_html",
            "plain_text",
        }
    ):
        raise ValueError("derived identities require a supported feed representation")
    revision = source_revision_id(record, profile=profile)
    if kind == "sanitized_html":
        artifact, parent = record.sanitized, record.original
        parent_id, parent_kind = revision, "source_revision"
    else:
        artifact, parent = record.plain_text, record.sanitized
        parent_id = derived_representation_id(record, "sanitized_html", profile=profile)
        parent_kind = "sanitized_html"
    return _id(
        DERIVED_NAMESPACE,
        {
            "source_revision_id": str(revision),
            "kind": kind,
            "output": {"domain": artifact.digest_domain, "sha256": artifact.sha256},
            "transformation": artifact.transformation.model_dump(mode="json"),
            "parent": {
                "kind": parent_kind,
                "id": str(parent_id),
                "domain": parent.digest_domain,
                "sha256": parent.sha256,
            },
        },
        profile,
    )


def artifact_association_id(
    artifact: ArtifactReference, *, profile: str = IDENTITY_PROFILE
) -> UUID:
    _check_profile(profile)
    record = _artifact.validate_python(artifact)
    return _id(ARTIFACT_NAMESPACE, record.model_dump(mode="json", exclude={"artifact_id"}), profile)


def evidence_metadata_digest(
    evidence: EvidenceRevisionV2, *, profile: str = IDENTITY_PROFILE
) -> EvidenceMetadataDigest:
    record = _record(evidence, profile)
    expected_logical = logical_item_id(
        record.provenance.source_id, record.provenance.source_key, profile=profile
    )
    if record.logical_item_id != expected_logical or record.evidence_id != source_revision_id(
        record, profile=profile
    ):
        raise ValueError("assign computed logical/source revision IDs before metadata digest")
    digest = compute_digest(
        "evidence-metadata-json-v1", record.model_dump(mode="json", exclude={"metadata_digest"})
    )
    return EvidenceMetadataDigest(domain=digest.domain, sha256=digest.sha256)


def evidence_association_id(
    evidence: EvidenceRevisionV2, *, profile: str = IDENTITY_PROFILE
) -> UUID:
    record = _record(evidence, profile)
    digest = evidence_metadata_digest(record, profile=profile)
    if record.metadata_digest != digest:
        raise ValueError("evidence metadata digest does not match the supplied bundle")
    return _id(ASSOCIATION_NAMESPACE, {"domain": digest.domain, "sha256": digest.sha256}, profile)


def processing_manifest_digest(
    manifest: ProcessingManifest, *, profile: str = IDENTITY_PROFILE
) -> ManifestDigest:
    _check_profile(profile)
    record = ProcessingManifest.model_validate(manifest)
    digest = compute_digest(
        "processing-manifest-json-v1",
        record.model_dump(mode="json", exclude={"manifest_id", "digest"}),
    )
    return ManifestDigest(domain=digest.domain, sha256=digest.sha256)


def processing_manifest_id(
    manifest: ProcessingManifest, *, profile: str = IDENTITY_PROFILE
) -> UUID:
    record = ProcessingManifest.model_validate(manifest)
    digest = processing_manifest_digest(record, profile=profile)
    if record.digest != digest:
        raise ValueError("manifest digest does not match the supplied manifest")
    return _id(MANIFEST_NAMESPACE, {"domain": digest.domain, "sha256": digest.sha256}, profile)


def retrieval_observation_id(
    observation: EvidenceObservation, *, profile: str = IDENTITY_PROFILE
) -> UUID:
    _check_profile(profile)
    record = EvidenceObservation.model_validate(observation)
    return _id(
        OBSERVATION_NAMESPACE, record.model_dump(mode="json", exclude={"observation_id"}), profile
    )
