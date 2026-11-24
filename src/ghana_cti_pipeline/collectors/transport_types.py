"""Transport-only inputs/results; M1 wire contracts remain unchanged."""

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from ghana_cti_pipeline.core.retrieval import ReceivedResponse, RetrievalOutcome

RSS_LIMIT = 6 * 1024**2
KEV_LIMIT = 8 * 1024**2
HEADER_LIMIT = 32 * 1024
DAILY_LIMIT = 512 * 1024**2


class TransportInputError(ValueError):
    """Bounded safe configuration code; never include supplied input."""


class TransportError(Exception):
    def __init__(self, code, *, retryable=False):
        if code not in {
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
        }:
            code = "protocol_error"
        super().__init__(code)
        self.code = code
        self.retryable = retryable is True and code in {"timeout", "connection_error", "http_error"}


def header_value(value):
    if value is not None and (
        type(value) is not str
        or not 1 <= len(value) <= 1024
        or not value.strip()
        or any(not 32 <= ord(c) <= 126 for c in value)
    ):
        raise TransportInputError("protocol_error")
    return value


class Clock(Protocol):
    def monotonic(self) -> float: ...
    def utcnow(self) -> datetime: ...
    def sleep(self, seconds: float) -> None: ...


@dataclass(frozen=True)
class Conditional:
    representation: ReceivedResponse
    etag: str | None = None
    last_modified: str | None = None

    def __post_init__(self):
        if not isinstance(self.representation, ReceivedResponse):
            raise TransportInputError("protocol_error")
        try:
            ReceivedResponse.model_validate(self.representation)
        except ValueError:
            raise TransportInputError("protocol_error") from None
        header_value(self.etag)
        header_value(self.last_modified)
        if self.etag is None and self.last_modified is None:
            raise TransportInputError("protocol_error")


@dataclass(frozen=True)
class TransportRequest:
    source_id: str
    url: str
    approved_urls: tuple[str, ...]
    limit_class: str
    version: str
    contact_url: str
    conditional: Conditional | None = None

    def __post_init__(self):
        if (
            type(self.source_id) is not str
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,255}", self.source_id)
            or type(self.limit_class) is not str
            or self.limit_class not in {"rss", "kev"}
            or type(self.version) is not str
            or not 1 <= len(self.version) <= 64
            or not re.fullmatch(r"[0-9]+\.[0-9]+[A-Za-z0-9.-]{0,48}", self.version)
            or type(self.approved_urls) is not tuple
            or not 1 <= len(self.approved_urls) <= 16
            or (self.conditional is not None and not isinstance(self.conditional, Conditional))
        ):
            raise TransportInputError("protocol_error")

    @property
    def body_limit(self):
        return RSS_LIMIT if self.limit_class == "rss" else KEV_LIMIT


@dataclass
class TransportBudget:
    attempts_remaining: int
    seconds_remaining: float
    bytes_remaining: int

    def __post_init__(self):
        if (
            type(self.attempts_remaining) is not int
            or not 0 <= self.attempts_remaining <= 3
            or type(self.seconds_remaining) not in {int, float}
            or not math.isfinite(self.seconds_remaining)
            or not 0 <= self.seconds_remaining <= 180
            or type(self.bytes_remaining) is not int
            or not 0 <= self.bytes_remaining <= DAILY_LIMIT
        ):
            raise TransportInputError("protocol_error")

    def charge(self, count):
        if count > self.bytes_remaining:
            raise TransportError("body_limit")
        self.bytes_remaining -= count


@dataclass(frozen=True)
class TransportResult:
    outcomes: tuple[RetrievalOutcome, ...]
    disposition: str
    body: bytes | None = field(default=None, repr=False)
    next_eligible_at: datetime | None = None


def remaining(clock, deadline, cap):
    seconds = min(cap, deadline - clock.monotonic())
    if seconds <= 0:
        raise TransportError("timeout", retryable=True)
    return seconds


def retrieval_id(factory, used):
    value = factory()
    if not isinstance(value, UUID) or value in used:
        raise TransportInputError("protocol_error")
    used.add(value)
    return value
