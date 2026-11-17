"""Backend-independent evidence access; no public artifact storage."""

from typing import Protocol
from uuid import UUID

from ghana_cti_pipeline.core.models import EvidenceRecord


class EvidenceRepository(Protocol):
    def get(self, evidence_id: UUID) -> EvidenceRecord | None:
        """Return one record or None when absent."""
        ...

    def add(self, record: EvidenceRecord) -> None:
        """Identical ID/content is a no-op; conflicting content raises ValueError.

        Must preserve the entire record and enforce private storage for restricted
        or unclassified evidence. No backend implements this contract yet.
        """
        ...
