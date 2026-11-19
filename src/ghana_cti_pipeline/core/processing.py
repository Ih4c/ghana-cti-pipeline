"""Processing manifests describe a bounded batch; they never advance checkpoints."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from ghana_cti_pipeline.core.artifacts import (
    ArtifactReference,
    CatalogEntryArtifact,
    OriginalHTMLArtifact,
    PlainTextArtifact,
    ResponseArtifact,
    SanitizedHTMLArtifact,
    validate_artifact_graph,
)
from ghana_cti_pipeline.core.evidence import EvidenceMetadataDigest, validate_response_reference
from ghana_cti_pipeline.core.evidence_values import (
    SHA256,
    EvidenceContract,
    Identifier,
    Locator,
    Mode,
    PolicyReference,
    Version,
)
from ghana_cti_pipeline.core.retrieval import ReceivedResponse


class _ManifestItem(EvidenceContract):
    evidence_id: UUID
    evidence_kind: Literal["hybrid"]
    evidence_schema_version: Literal["2.0"]
    evidence_digest: EvidenceMetadataDigest
    locator: Locator


class CatalogManifestItem(_ManifestItem):
    mode: Literal["catalog_entry"]
    entry_id: UUID


class FeedManifestItem(_ManifestItem):
    mode: Literal["feed_full_text"]
    original_id: UUID
    sanitized_id: UUID
    plain_text_id: UUID


ManifestItem = Annotated[CatalogManifestItem | FeedManifestItem, Field(discriminator="mode")]


class ManifestDigest(EvidenceContract):
    sha256: SHA256
    domain: Literal["processing-manifest-json-v1"]


class ProcessingManifest(EvidenceContract):
    kind: Literal["processing_manifest"]
    manifest_id: UUID
    mode: Mode
    policy: PolicyReference
    retrieval: ReceivedResponse
    request_variant_id: Identifier
    adapter_version: Version
    parser_version: Version
    processing_profile: Version
    completeness: Literal["complete", "incomplete"]
    expected_item_count: Annotated[int, Field(strict=True, ge=0, le=10000)]
    items: Annotated[tuple[ManifestItem, ...], Field(max_length=10000)]
    response: ResponseArtifact
    artifacts: Annotated[tuple[ArtifactReference, ...], Field(max_length=10000)]
    digest: ManifestDigest

    @model_validator(mode="after")
    def check_batch(self) -> Self:
        validate_response_reference(self.retrieval, self.response)
        if self.retrieval.source_id != self.policy.source_id:
            raise ValueError("manifest source and policy disagree")
        validate_artifact_graph((self.response, *self.artifacts), self.policy)
        if len(self.items) > self.expected_item_count or (
            self.completeness == "complete" and len(self.items) != self.expected_item_count
        ):
            raise ValueError("processing completeness and item count disagree")
        if self.mode == "feed_full_text" and (
            self.expected_item_count > 500
            or max(
                self.retrieval.body_metadata.decoded_bytes,
                self.retrieval.body_metadata.transferred_bytes,
            )
            > 2 * 1024 * 1024
        ):
            raise ValueError("RSS batch count/response cap exceeded")
        if len({item.evidence_id for item in self.items}) != len(self.items) or len(
            {item.locator for item in self.items}
        ) != len(self.items):
            raise ValueError("duplicate evidence ID or item locator")
        by_id = {a.artifact_id: a for a in self.artifacts}
        used = set()
        for item in self.items:
            if item.mode != self.mode:
                raise ValueError("manifest and item representation disagree")
            if isinstance(item, CatalogManifestItem):
                entry = by_id.get(item.entry_id)
                if not isinstance(entry, CatalogEntryArtifact) or entry.locator != item.locator:
                    raise ValueError("missing or contradictory catalog backing")
                used.add(item.entry_id)
            else:
                original = by_id.get(item.original_id)
                sanitized = by_id.get(item.sanitized_id)
                plain = by_id.get(item.plain_text_id)
                if not (
                    isinstance(original, OriginalHTMLArtifact)
                    and isinstance(sanitized, SanitizedHTMLArtifact)
                    and isinstance(plain, PlainTextArtifact)
                    and original.locator == item.locator
                    and sanitized.parent.artifact_id == original.artifact_id
                    and plain.parent.artifact_id == sanitized.artifact_id
                ):
                    raise ValueError("missing or contradictory full-text backing")
                used.update((item.original_id, item.sanitized_id, item.plain_text_id))
        if used != set(by_id):
            raise ValueError("manifest contains artifacts not associated with its items")
        caps = (
            {"catalog_entry": 8 * 1024 * 1024}
            if self.mode == "catalog_entry"
            else {
                "original_html": 2 * 1024 * 1024,
                "sanitized_html": 2 * 1024 * 1024,
                "plain_text": 2 * 1024 * 1024,
            }
        )
        for kind, cap in caps.items():
            if sum(a.byte_count for a in self.artifacts if a.kind == kind) > cap:
                raise ValueError("aggregate artifact byte cap exceeded")
        return self
