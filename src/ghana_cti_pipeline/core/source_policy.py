"""Declared source policy scope and deadlines, not authorization enforcement."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from ghana_cti_pipeline.core.artifacts import ArtifactKind
from ghana_cti_pipeline.core.evidence_values import (
    EvidenceContract,
    Metadata,
    Mode,
    PolicyReference,
    ReferenceURL,
    Timestamp,
)


class RetentionDeadlines(EvidenceContract):
    response: Timestamp
    original: Timestamp
    derived: Timestamp
    metadata: Timestamp
    digests: Timestamp
    audit: Timestamp
    backups: Timestamp


class SourcePolicy(EvidenceContract):
    kind: Literal["source_policy"]
    reference: PolicyReference
    endpoint: ReferenceURL
    mode: Mode
    operator: Metadata
    purpose: Metadata
    basis_status: Literal["unresolved", "documented"] = "unresolved"
    basis_references: Annotated[tuple[ReferenceURL, ...], Field(max_length=32)] = ()
    reviewed_at: Timestamp | None = None
    permitted_artifacts: Annotated[tuple[ArtifactKind, ...], Field(max_length=5)] = ()
    permitted_processing: Annotated[
        tuple[
            Literal[
                "retrieve", "retain", "sanitize_html", "extract_text", "internal_use", "backup"
            ],
            ...,
        ],
        Field(max_length=6),
    ] = ()
    conditions: Metadata  # Access, sharing, quotas, deletion and backup conditions as declared.
    effective_at: Timestamp
    expires_at: Timestamp
    retention: RetentionDeadlines

    @model_validator(mode="after")
    def check_metadata(self) -> Self:
        if self.expires_at <= self.effective_at:
            raise ValueError("policy expiration must follow its effective time")
        if self.basis_status == "documented" and (
            not self.basis_references or self.reviewed_at is None
        ):
            raise ValueError("documented basis needs references and a review date")
        for values in (self.permitted_artifacts, self.permitted_processing, self.basis_references):
            if len(set(values)) != len(values):
                raise ValueError("policy scope and references cannot contain duplicates")
        expected = (
            {"http_response", "catalog_entry"}
            if self.mode == "catalog_entry"
            else {
                "http_response",
                "original_html",
                "sanitized_html",
                "plain_text",
            }
        )
        if not set(self.permitted_artifacts) <= expected:
            raise ValueError("artifact scope contradicts the declared representation")
        if self.mode == "catalog_entry" and {"sanitize_html", "extract_text"} & set(
            self.permitted_processing
        ):
            raise ValueError("catalog mode does not use HTML transformations")
        if any(
            getattr(self.retention, name) < self.effective_at
            for name in type(self.retention).model_fields
            if name != "schema_version"
        ):
            raise ValueError("retention deadline precedes policy effective time")
        return self
