"""Additive offline storage inputs; existing core wire contracts are unchanged."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from ghana_cti_pipeline.core.artifacts import Transformation
from ghana_cti_pipeline.core.digests import canonical_json
from ghana_cti_pipeline.core.evidence_values import (
    EvidenceContract,
    Identifier,
    PolicyReference,
    ReferenceURL,
    Timestamp,
    Version,
)
from ghana_cti_pipeline.core.processing import ProcessingManifest


class StoreError(ValueError):
    """Stable safe code, never a payload, SQL statement or raw validation error."""


def serialized(record: EvidenceContract) -> str:
    return canonical_json(record.model_dump(mode="json")).decode("utf-8")


class CheckpointContext(EvidenceContract):
    policy: PolicyReference
    endpoint: ReferenceURL
    request_variant_id: Identifier
    adapter_version: Version
    parser_version: Version
    processing_profile: Version
    transformations: Annotated[tuple[Transformation, ...], Field(max_length=10000)] = ()

    @classmethod
    def from_manifest(cls, manifest: ProcessingManifest):
        manifest = ProcessingManifest.model_validate(manifest)
        transforms = {
            serialized(a.transformation): a.transformation
            for a in manifest.artifacts
            if a.kind in {"sanitized_html", "plain_text"}
        }
        return cls(
            policy=manifest.policy,
            endpoint=manifest.retrieval.requested_url,
            request_variant_id=manifest.request_variant_id,
            adapter_version=manifest.adapter_version,
            parser_version=manifest.parser_version,
            processing_profile=manifest.processing_profile,
            transformations=tuple(transforms[key] for key in sorted(transforms)),
        )

    def selector(self) -> str:
        return canonical_json(
            [self.policy.source_id, self.endpoint, self.request_variant_id]
        ).decode("utf-8")


class StoredCheckpoint(EvidenceContract):
    context: CheckpointContext
    manifest_id: UUID
    representation_retrieval_id: UUID
    last_retrieval_id: UUID
    last_checked_at: Timestamp
    etag: Annotated[str, Field(max_length=1024)] | None = None
    last_modified: Annotated[str, Field(max_length=1024)] | None = None
