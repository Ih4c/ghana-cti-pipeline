"""Immutable artifact references and separate lifecycle assertions, never bodies."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from ghana_cti_pipeline.core.evidence_values import (
    SHA256,
    EvidenceContract,
    Locator,
    PolicyReference,
    Timestamp,
    Version,
)

ArtifactKind = Literal[
    "http_response", "original_html", "sanitized_html", "plain_text", "catalog_entry"
]
DigestDomain = Literal[
    "decoded-http-entity-v1",
    "feed-field-html-utf8-v1",
    "sanitized-html-utf8-v1",
    "plain-text-utf8-v1",
    "catalog-entry-json-v1",
]
DOMAINS = {
    "http_response": "decoded-http-entity-v1",
    "original_html": "feed-field-html-utf8-v1",
    "sanitized_html": "sanitized-html-utf8-v1",
    "plain_text": "plain-text-utf8-v1",
    "catalog_entry": "catalog-entry-json-v1",
}


class ArtifactParent(EvidenceContract):
    artifact_id: UUID
    kind: ArtifactKind
    sha256: SHA256
    digest_domain: DigestDomain

    @model_validator(mode="after")
    def check_domain(self) -> Self:
        if self.digest_domain != DOMAINS[self.kind]:
            raise ValueError("parent kind and digest domain disagree")
        return self


class Transformation(EvidenceContract):
    operation: Literal["sanitize_html", "extract_text"]
    implementation_version: Version
    parser_version: Version
    configuration_sha256: SHA256


class _Artifact(ArtifactParent):
    policy: PolicyReference
    byte_count: Annotated[int, Field(strict=True, ge=1, le=8 * 1024 * 1024)]


class ResponseArtifact(_Artifact):
    kind: Literal["http_response"]
    digest_domain: Literal["decoded-http-entity-v1"]
    retrieval_id: UUID
    byte_count: Annotated[int, Field(strict=True, ge=0, le=8 * 1024 * 1024)]


class _ChildArtifact(_Artifact):
    parent: ArtifactParent

    @model_validator(mode="after")
    def check_parent(self) -> Self:
        expected = {
            "original_html": "http_response",
            "catalog_entry": "http_response",
            "sanitized_html": "original_html",
            "plain_text": "sanitized_html",
        }[self.kind]
        if self.parent.kind != expected or self.parent.artifact_id == self.artifact_id:
            raise ValueError("invalid derivation parent")
        return self


class OriginalHTMLArtifact(_ChildArtifact):
    kind: Literal["original_html"]
    digest_domain: Literal["feed-field-html-utf8-v1"]
    byte_count: Annotated[int, Field(strict=True, ge=1, le=1024 * 1024)]
    locator: Locator
    source_field: Literal["content:encoded", "description"]


class CatalogEntryArtifact(_ChildArtifact):
    kind: Literal["catalog_entry"]
    digest_domain: Literal["catalog-entry-json-v1"]
    locator: Locator


class _DerivedArtifact(_ChildArtifact):
    byte_count: Annotated[int, Field(strict=True, ge=1, le=1024 * 1024)]
    transformation: Transformation

    @model_validator(mode="after")
    def check_operation(self) -> Self:
        expected = "sanitize_html" if self.kind == "sanitized_html" else "extract_text"
        if self.transformation.operation != expected:
            raise ValueError("artifact kind and transformation operation disagree")
        return self


class SanitizedHTMLArtifact(_DerivedArtifact):
    kind: Literal["sanitized_html"]
    digest_domain: Literal["sanitized-html-utf8-v1"]


class PlainTextArtifact(_DerivedArtifact):
    kind: Literal["plain_text"]
    digest_domain: Literal["plain-text-utf8-v1"]


ArtifactReference = Annotated[
    ResponseArtifact
    | OriginalHTMLArtifact
    | SanitizedHTMLArtifact
    | PlainTextArtifact
    | CatalogEntryArtifact,
    Field(discriminator="kind"),
]


def validate_artifact_graph(artifacts: tuple[_Artifact, ...], policy: PolicyReference) -> None:
    """Check only supplied descriptors, not stored content, rights or availability."""
    by_id = {a.artifact_id: a for a in artifacts}
    if len(by_id) != len(artifacts):
        raise ValueError("artifact IDs must be unique within an association")
    for artifact in artifacts:
        if artifact.policy != policy:
            raise ValueError("artifact policy association mismatch")
        if isinstance(artifact, _ChildArtifact):
            parent = by_id.get(artifact.parent.artifact_id)
            if parent is None or any(
                getattr(parent, field) != getattr(artifact.parent, field)
                for field in ("kind", "sha256", "digest_domain")
            ):
                raise ValueError("unresolved or contradictory parent descriptor")


class ArtifactAvailability(EvidenceContract):
    """A dated lifecycle assertion; never embedded mutable state in evidence."""

    kind: Literal["artifact_availability"]
    artifact_id: UUID
    policy: PolicyReference
    state: Literal["available", "expired", "deleted", "unavailable"]
    recorded_at: Timestamp
    retention_until: Timestamp

    @model_validator(mode="after")
    def check_expiration(self) -> Self:
        if self.state == "available" and self.recorded_at >= self.retention_until:
            raise ValueError("available assertion cannot outlive its retention deadline")
        if self.state == "expired" and self.recorded_at < self.retention_until:
            raise ValueError("expired assertion precedes its retention deadline")
        return self
