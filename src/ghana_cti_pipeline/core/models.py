"""V1 contracts only. These models neither collect nor publish intelligence."""

from collections.abc import Mapping
from copy import deepcopy
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import (
    AnyHttpUrl,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    field_validator,
    model_validator,
)

Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
EvidenceIDs = Annotated[tuple[UUID, ...], Field(min_length=1)]
_http_url = TypeAdapter(AnyHttpUrl)


class Contract(BaseModel):
    """Immutable records; schema changes require an explicit contract version."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["1.0"] = "1.0"

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> Self:
        """Reconstruct and validate copies, including updates, without mutating the original."""
        data = self.model_dump(round_trip=True)
        if update is not None:
            data.update(update)
        return type(self).model_validate(deepcopy(data) if deep else data)


class TLP(StrEnum):
    CLEAR = "TLP:CLEAR"
    GREEN = "TLP:GREEN"
    AMBER = "TLP:AMBER"
    AMBER_STRICT = "TLP:AMBER+STRICT"
    RED = "TLP:RED"


class Confidence(StrEnum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GhanaRelevance(StrEnum):
    UNKNOWN = "unknown"
    POSSIBLE_EXPOSURE = "possible_exposure"
    CONFIRMED_TARGETING = "confirmed_targeting"


class Provenance(Contract):
    source_id: Text
    publisher: Text
    original_url: Text
    canonical_url: Text | None = None
    source_item_id: Text | None = None
    published_at: AwareDatetime | None = None
    observed_at: AwareDatetime | None = None
    retrieved_at: AwareDatetime

    @field_validator("original_url", "canonical_url")
    @classmethod
    def validate_reference_url(cls, value: str | None) -> str | None:
        # Validate without normalizing away the publisher's exact reference.
        if value is not None:
            parsed = _http_url.validate_python(value)
            if value != value.strip() or parsed.username or parsed.password:
                raise ValueError("reference URLs must omit credentials and surrounding whitespace")
        return value


class SourceItem(Contract):
    id: UUID
    provenance: Provenance
    title: Text
    excerpt: Text  # Untrusted source text; never instructions or verified analysis.
    tlp: TLP | None = None  # Unclassified is not publicly shareable.


class EvidenceRecord(Contract):
    id: UUID
    source_item: SourceItem
    excerpt_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    parent_evidence_ids: tuple[UUID, ...] = ()
    confidence: Confidence = Confidence.UNKNOWN

    @model_validator(mode="after")
    def verify_excerpt_digest(self) -> "EvidenceRecord":
        expected = sha256(self.source_item.excerpt.encode("utf-8")).hexdigest()
        if self.excerpt_sha256 != expected:
            raise ValueError("excerpt_sha256 must match the exact UTF-8 source excerpt")
        return self


class Indicator(Contract):
    id: UUID
    kind: Literal["ipv4", "ipv6", "domain", "url", "email", "md5", "sha1", "sha256"]
    value: Text  # Inert candidate; type-specific validation belongs to later enrichment.
    evidence_ids: EvidenceIDs
    observed_at: AwareDatetime | None = None
    confidence: Confidence = Confidence.UNKNOWN
    tlp: TLP | None = None
    validation_status: Literal["pending"] = "pending"


class Assessment(Contract):
    id: UUID
    revision: Annotated[int, Field(strict=True, ge=1)] = 1
    author_id: Text
    author_type: Literal["human"] = "human"
    authored_at: AwareDatetime
    evidence_ids: EvidenceIDs
    observed_facts: tuple[Text, ...] = ()
    hypotheses: tuple[Text, ...] = ()
    unknowns: tuple[Text, ...] = ()
    ghana_relevance: GhanaRelevance = GhanaRelevance.UNKNOWN
    ghana_relevance_rationale: Text | None = None
    confidence: Confidence = Confidence.UNKNOWN
    tlp: TLP | None = None

    @model_validator(mode="after")
    def require_relevance_rationale(self) -> "Assessment":
        if self.ghana_relevance != GhanaRelevance.UNKNOWN and not self.ghana_relevance_rationale:
            raise ValueError(
                "Ghana relevance claims require an analyst's evidence-linked rationale"
            )
        return self


class ReviewDecision(Contract):
    """Append-only decision intent tied to one revision; no approval side effects."""

    id: UUID
    subject_type: Literal["assessment", "report"]
    subject_id: UUID
    subject_revision: Annotated[int, Field(strict=True, ge=1)]
    reviewer_id: Text
    reviewer_type: Literal["human"] = "human"
    decided_at: AwareDatetime
    decision: Literal["approved", "rejected", "changes_requested"]
    rationale: Text


class Report(Contract):
    """Human-authored draft only; approval and publication workflows are deferred."""

    id: UUID
    revision: Annotated[int, Field(strict=True, ge=1)] = 1
    author_id: Text
    author_type: Literal["human"] = "human"
    authored_at: AwareDatetime
    title: Text
    body_markdown: Text
    evidence_ids: EvidenceIDs
    assessment_ids: tuple[UUID, ...] = ()
    tlp: TLP | None = None
    status: Literal["draft"] = "draft"
