"""V2 evidence associations. Source content remains in referenced artifacts."""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, model_validator

from ghana_cti_pipeline.core.artifacts import (
    CatalogEntryArtifact,
    OriginalHTMLArtifact,
    PlainTextArtifact,
    ResponseArtifact,
    SanitizedHTMLArtifact,
    validate_artifact_graph,
)
from ghana_cti_pipeline.core.evidence_values import (
    SHA256,
    CalendarDate,
    EvidenceContract,
    Identifier,
    Locator,
    Metadata,
    PolicyReference,
    ReferenceURL,
    Timestamp,
    Version,
)
from ghana_cti_pipeline.core.models import TLP
from ghana_cti_pipeline.core.retrieval import ComputedDigest, ReceivedResponse


class PublicationDate(EvidenceContract):
    supplied_text: Annotated[str, Field(strict=True, max_length=8192)] | None = None
    precision: Literal["unknown", "date", "timestamp"]
    parse_outcome: Literal["missing", "invalid", "parsed"]
    date: CalendarDate | None = None
    timestamp: Timestamp | None = None

    @model_validator(mode="after")
    def check_precision(self) -> Self:
        if self.precision == "unknown":
            if (
                self.date is not None
                or self.timestamp is not None
                or self.parse_outcome == "parsed"
            ):
                raise ValueError("unknown publication date cannot claim a parsed value")
            if (self.supplied_text is None) != (self.parse_outcome == "missing"):
                raise ValueError("missing/invalid outcome must match supplied date text")
        elif (
            self.parse_outcome != "parsed"
            or self.supplied_text is None
            or not self.supplied_text.strip()
            or (self.date is not None) != (self.precision == "date")
            or (self.timestamp is not None) != (self.precision == "timestamp")
        ):
            raise ValueError("publication precision and parsed value disagree")
        return self


class NativeKey(EvidenceContract):
    kind: Literal["native_id"]
    value: Metadata


class URLKey(EvidenceContract):
    kind: Literal["original_url"]
    value: ReferenceURL


SourceKey = Annotated[NativeKey | URLKey, Field(discriminator="kind")]


class EvidenceProvenance(EvidenceContract):
    source_id: Identifier
    publisher: Metadata
    publisher_origin: Literal["supplied", "configured"]
    byline: Metadata | None = None
    byline_origin: Literal["supplied", "configured"] | None = None
    source_key: SourceKey
    original_url: ReferenceURL | None = None
    publication: PublicationDate
    first_acquisition: ReceivedResponse
    request_variant_id: Identifier
    locator: Locator
    adapter_version: Version
    parser_version: Version
    identity_profile: Version
    policy: PolicyReference

    @model_validator(mode="after")
    def check_provenance(self) -> Self:
        if (
            self.source_id != self.first_acquisition.source_id
            or self.source_id != self.policy.source_id
        ):
            raise ValueError("provenance source identities disagree")
        if (self.byline is None) != (self.byline_origin is None):
            raise ValueError("byline requires an explicit origin")
        if isinstance(self.source_key, URLKey) and self.source_key.value != self.original_url:
            raise ValueError("URL fallback must equal the exact original URL")
        return self


def validate_response_reference(receipt: ReceivedResponse, artifact: ResponseArtifact) -> None:
    if artifact.retrieval_id != receipt.retrieval_id:
        raise ValueError("response artifact must name the supplied 200 retrieval")
    if artifact.byte_count != receipt.body_metadata.decoded_bytes:
        raise ValueError("response artifact and complete decoded byte count disagree")
    digest = receipt.body_metadata.digest
    if isinstance(digest, ComputedDigest) and artifact.sha256 != digest.sha256:
        raise ValueError("response artifact and declared receipt digest disagree")


class EvidenceMetadataDigest(EvidenceContract):
    sha256: SHA256
    domain: Literal["evidence-metadata-json-v1"]


class _EvidenceRevision(EvidenceContract):
    schema_version: Literal["2.0"] = "2.0"
    kind: Literal["hybrid"]
    evidence_id: UUID
    logical_item_id: UUID
    metadata_digest: EvidenceMetadataDigest
    provenance: EvidenceProvenance
    response: ResponseArtifact
    confidence: Literal["unknown"] = "unknown"
    tlp: TLP | None = None  # Caller-supplied only, never a collection-derived marking.

    @model_validator(mode="after")
    def check_response(self) -> Self:
        validate_response_reference(self.provenance.first_acquisition, self.response)
        return self


class CatalogContext(EvidenceContract):
    title: Metadata
    catalog_version: Version
    date_released: Timestamp
    count: Annotated[int, Field(strict=True, ge=1, le=10000)]


class CatalogFields(EvidenceContract):
    """Known KEV projection; the original entry artifact preserves complete structure."""

    cveID: Metadata
    vendorProject: Metadata
    product: Metadata
    vulnerabilityName: Metadata
    dateAdded: CalendarDate
    shortDescription: Metadata
    requiredAction: Metadata
    dueDate: CalendarDate
    knownRansomwareCampaignUse: Metadata
    notes: Annotated[str, Field(strict=True, max_length=8192)]
    cwes: Annotated[tuple[Metadata, ...], Field(max_length=128)] = ()


class CatalogEvidenceRevision(_EvidenceRevision):
    mode: Literal["catalog_entry"]
    catalog: CatalogContext
    fields: CatalogFields
    entry: CatalogEntryArtifact

    @model_validator(mode="after")
    def check_entry(self) -> Self:
        validate_artifact_graph((self.response, self.entry), self.provenance.policy)
        if self.entry.locator != self.provenance.locator:
            raise ValueError("catalog locator mismatch")
        if (
            not isinstance(self.provenance.source_key, NativeKey)
            or self.provenance.source_key.value != self.fields.cveID
        ):
            raise ValueError("catalog native key must preserve cveID")
        return self


class FeedFullTextEvidenceRevision(_EvidenceRevision):
    mode: Literal["feed_full_text"]
    title: Metadata
    original: OriginalHTMLArtifact
    sanitized: SanitizedHTMLArtifact
    plain_text: PlainTextArtifact

    @model_validator(mode="after")
    def check_full_text(self) -> Self:
        validate_artifact_graph(
            (self.response, self.original, self.sanitized, self.plain_text),
            self.provenance.policy,
        )
        if self.provenance.original_url is None:
            raise ValueError("feed evidence requires the supplied original article URL")
        if self.original.locator != self.provenance.locator:
            raise ValueError("feed field locator mismatch")
        body = self.provenance.first_acquisition.body_metadata
        if max(body.decoded_bytes, body.transferred_bytes) > 6 * 1024 * 1024:
            raise ValueError("RSS response exceeds the 6 MiB cap")
        return self


EvidenceRevisionV2 = Annotated[
    CatalogEvidenceRevision | FeedFullTextEvidenceRevision,
    Field(discriminator="mode"),
]
