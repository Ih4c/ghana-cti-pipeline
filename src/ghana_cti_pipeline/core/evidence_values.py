"""Bounded values for additive evidence contracts; no payload processing."""

import re
import unicodedata
from datetime import date, datetime
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    AwareDatetime,
    BeforeValidator,
    ConfigDict,
    StringConstraints,
    TypeAdapter,
)

from ghana_cti_pipeline.core.models import Contract

Identifier = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=256, pattern=r"\S")
]
Version = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=128, pattern=r"\S")
]
Metadata = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=8192, pattern=r"\S")
]
Locator = Annotated[
    str, StringConstraints(strict=True, min_length=1, max_length=4096, pattern=r"\S")
]
SHA256 = Annotated[
    str, StringConstraints(strict=True, min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
]
Mode = Literal["catalog_entry", "feed_full_text"]
_http = TypeAdapter(AnyHttpUrl)


def reference_url(value: str) -> str:
    if any(c.isspace() or unicodedata.category(c) in {"Cc", "Cf"} for c in value):
        raise ValueError("reference URL contains whitespace or controls")
    if "\\" in value or re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ValueError("reference URL contains an invalid escape")
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username is not None:
        raise ValueError("reference URL requires HTTP(S) authority without credentials")
    _http.validate_python(value)
    return value  # An inert reference, not a transport allowlist or normalization step.


def timestamp_input(value: object) -> object:
    if isinstance(value, datetime) or (
        isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}[Tt ]", value)
    ):
        return value
    raise ValueError("timestamp requires an aware datetime or explicit-offset ISO string")


def date_input(value: object) -> object:
    if type(value) is date or (
        isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)
    ):
        return value
    raise ValueError("date requires a calendar date, without inferred time or epoch")


ReferenceURL = Annotated[
    str,
    StringConstraints(strict=True, min_length=1, max_length=4096),
    AfterValidator(reference_url),
]
Timestamp = Annotated[AwareDatetime, BeforeValidator(timestamp_input)]
CalendarDate = Annotated[date, BeforeValidator(date_input)]


class EvidenceContract(Contract):
    model_config = ConfigDict(revalidate_instances="always")


class PolicyReference(EvidenceContract):
    source_id: Identifier
    policy_id: Identifier
    policy_version: Version
