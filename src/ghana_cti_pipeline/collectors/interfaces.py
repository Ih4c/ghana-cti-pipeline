"""Fetch/parse separation permits parsing tests without network access."""

from dataclasses import dataclass
from typing import Protocol

from ghana_cti_pipeline.core.models import Provenance, SourceItem


@dataclass(frozen=True)
class FetchedDocument:
    provenance: Provenance
    body: bytes
    media_type: str


class CollectorError(Exception):
    """Source-local failure with a safe code, never an untrusted payload in logs."""

    def __init__(self, *, source_id: str, code: str, retryable: bool = False) -> None:
        self.source_id = source_id
        self.code = code
        self.retryable = retryable
        super().__init__("collector operation failed")


class Collector(Protocol):
    source_id: str

    def fetch(self) -> FetchedDocument:
        """Fetch one bounded document; raise CollectorError on source-local failure."""
        ...

    def parse(self, document: FetchedDocument) -> tuple[SourceItem, ...]:
        """Parse without I/O; retain provenance and treat all body text as untrusted."""
        ...
