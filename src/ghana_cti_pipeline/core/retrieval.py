"""M1-01 metadata only: no fetching, hashing, retention or evidence resolution."""

import re
import unicodedata
from datetime import datetime
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    AwareDatetime,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    TypeAdapter,
    model_validator,
)

from ghana_cti_pipeline.core.models import Contract

_http_url = TypeAdapter(AnyHttpUrl)


def _no_controls(value: str) -> str:
    if any(unicodedata.category(char) in {"Cc", "Cf"} for char in value):
        raise ValueError("control characters are not permitted")
    return value


def _https_reference(value: str) -> str:
    _no_controls(value)
    if any(char.isspace() for char in value) or "\\" in value or "#" in value:
        raise ValueError("URL must omit whitespace, backslashes and fragments")
    if re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ValueError("URL contains an invalid percent escape")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.netloc or parts.username is not None:
        raise ValueError("URL must have an HTTPS authority without credentials")
    _http_url.validate_python(value)
    return value  # Validate syntax without normalizing the supplied reference.


def _timestamp_input(value: object) -> object:
    if isinstance(value, datetime):
        return value  # AwareDatetime subsequently rejects naive datetime objects.
    if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}[Tt ]", value):
        return value
    raise ValueError("timestamp must be a datetime or ISO string with an explicit offset")


def _integer_status(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("HTTP status must be an integer")
    return value


_Identifier = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=256, pattern=r"\S")
]
_ShortText = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=128, pattern=r"\S")
]
_Locator = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=4096, pattern=r"\S")
]
_Header = Annotated[
    str,
    StringConstraints(strict=True, min_length=1, max_length=1024, pattern=r"\S"),
    AfterValidator(_no_controls),
]
_URL = Annotated[
    str,
    StringConstraints(strict=True, min_length=1, max_length=4096),
    AfterValidator(_https_reference),
]
_Timestamp = Annotated[AwareDatetime, BeforeValidator(_timestamp_input)]
_ByteCount = Annotated[int, Field(strict=True, ge=0, le=8 * 1024 * 1024)]
_SHA256 = Annotated[
    str, StringConstraints(strict=True, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
]


class _Descriptor(Contract):
    # Revalidate supplied nested instances as well as dictionaries at trust boundaries.
    model_config = ConfigDict(revalidate_instances="always")


class ComputedDigest(_Descriptor):
    """A caller-declared digest, not a calculation or authenticity guarantee."""

    digest_state: Literal["computed"]
    sha256: _SHA256
    domain: Literal["decoded-http-entity-v1"]


class NotComputedDigest(_Descriptor):
    digest_state: Literal["not_computed"]
    sha256: None = None
    domain: None = None


ResponseDigest = Annotated[ComputedDigest | NotComputedDigest, Field(discriminator="digest_state")]


class ResponseBodyMetadata(_Descriptor):
    """Descriptor of a complete entity, with no raw bytes or retention claim."""

    kind: Literal["response_body_metadata"]
    decoded_bytes: _ByteCount
    transferred_bytes: _ByteCount
    media_type: _ShortText
    content_encoding: _ShortText
    digest: ResponseDigest


class _RetrievalAttempt(_Descriptor):
    retrieval_id: UUID
    source_id: _Identifier
    requested_url: _URL
    started_at: _Timestamp
    ended_at: _Timestamp

    @model_validator(mode="after")
    def check_time_order(self) -> Self:
        if self.ended_at < self.started_at:
            raise ValueError("ended_at must be at or after started_at")
        return self


class _HTTPResponse(_RetrievalAttempt):
    final_url: _URL
    redirect_urls: Annotated[tuple[_URL, ...], Field(max_length=3)] = ()
    returned_etag: _Header | None = None
    returned_last_modified: _Header | None = None
    cache_control: _Header | None = None
    vary: _Header | None = None

    @model_validator(mode="after")
    def check_redirect_destination(self) -> Self:
        expected = self.redirect_urls[-1] if self.redirect_urls else self.requested_url
        if self.final_url != expected:
            raise ValueError("final_url must match the final redirect or requested_url")
        return self


class ReceivedResponse(_HTTPResponse):
    """Complete 200 receipt; processing, storage and checkpoint success are separate."""

    kind: Literal["received_response"]
    status: Annotated[Literal[200], BeforeValidator(_integer_status)]
    body_metadata: ResponseBodyMetadata


class NotModifiedResponse(_HTTPResponse):
    """304 check; the declared 200 reference needs later cross-record validation."""

    kind: Literal["not_modified_response"]
    status: Annotated[Literal[304], BeforeValidator(_integer_status)]
    sent_etag: _Header | None = None
    sent_last_modified: _Header | None = None
    representation_retrieval_id: UUID

    @model_validator(mode="after")
    def require_sent_validator(self) -> Self:
        if self.sent_etag is None and self.sent_last_modified is None:
            raise ValueError("304 requires a sent ETag or Last-Modified validator")
        return self


FailureCode = Literal[
    "timeout",
    "connection_error",
    "tls_error",
    "unsafe_url",
    "redirect_limit",
    "proxy_disallowed",
    "header_limit",
    "body_limit",
    "content_decoding_error",
    "http_error",
    "protocol_error",
]


class RetrievalFailure(_RetrievalAttempt):
    """Safe failure vocabulary; even received 200/304 statuses may precede failure."""

    kind: Literal["retrieval_failure"]
    status: Annotated[int, Field(strict=True, ge=100, le=599)] | None = None
    code: FailureCode
    retryable: StrictBool


RetrievalOutcome = Annotated[
    ReceivedResponse | NotModifiedResponse | RetrievalFailure, Field(discriminator="kind")
]


class EvidenceObservation(_Descriptor):
    """Declared link to parsed-200 evidence; neither a resolver nor a V2 evidence model."""

    kind: Literal["evidence_observation"]
    observation_id: UUID
    retrieval_id: UUID
    evidence_id: UUID
    evidence_kind: Literal["v1", "hybrid"]
    evidence_schema_version: Literal["1.0", "2.0"]
    locator: _Locator
    adapter_version: _ShortText
    source_policy_id: _Identifier
    source_policy_version: _ShortText

    @model_validator(mode="after")
    def check_evidence_version(self) -> Self:
        expected = "1.0" if self.evidence_kind == "v1" else "2.0"
        if self.evidence_schema_version != expected:
            raise ValueError("evidence kind and schema version must agree")
        return self
