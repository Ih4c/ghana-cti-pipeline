"""Pure validation for offline writes and conditional-state eligibility."""

from datetime import UTC
from hashlib import sha256

from pydantic import TypeAdapter

from ghana_cti_pipeline.core.artifacts import ArtifactAvailability, ArtifactReference
from ghana_cti_pipeline.core.evidence_values import Timestamp
from ghana_cti_pipeline.core.identities import retrieval_observation_id
from ghana_cti_pipeline.core.retrieval import EvidenceObservation
from ghana_cti_pipeline.core.source_policy import SourcePolicy
from ghana_cti_pipeline.storage.records import StoreError

_timestamp = TypeAdapter(Timestamp)


def timestamp(value):
    return _timestamp.validate_python(value).astimezone(UTC)


def time_key(value) -> str:
    return timestamp(value).isoformat(timespec="microseconds")


def no_store(receipt) -> bool:
    return any(
        part.split("=", 1)[0].strip().lower() == "no-store"
        for part in (receipt.cache_control or "").split(",")
    )


def conditionals_supported(receipt) -> bool:
    return not no_store(receipt) and all(
        part.strip().lower() in {"accept-encoding", "user-agent", ""}
        for part in (receipt.vary or "").split(",")
    )


def retention_deadline(policy: SourcePolicy, artifact: ArtifactReference):
    group = {
        "http_response": "response",
        "catalog_entry": "original",
        "original_html": "original",
        "sanitized_html": "derived",
        "plain_text": "derived",
    }[artifact.kind]
    return getattr(policy.retention, group)


def validate_policy(policy, manifest, at):
    needed = {"retrieve", "retain", "internal_use"}
    if manifest.mode == "feed_full_text":
        needed |= {"sanitize_html", "extract_text"}
    if (
        policy.reference != manifest.policy
        or policy.endpoint != manifest.retrieval.requested_url
        or policy.mode != manifest.mode
        or policy.basis_status != "documented"
        or not policy.effective_at <= at < policy.expires_at
        or policy.reviewed_at is None
        or policy.reviewed_at > at
        or not needed <= set(policy.permitted_processing)
        or any(at >= getattr(policy.retention, name) for name in ("metadata", "digests", "audit"))
    ):
        raise StoreError("policy_denied")
    for artifact in (manifest.response, *manifest.artifacts):
        if artifact.kind not in policy.permitted_artifacts or at >= retention_deadline(
            policy, artifact
        ):
            raise StoreError("policy_denied")


def validate_bytes(artifact, body):
    if (
        type(body) is not bytes
        or len(body) != artifact.byte_count
        or sha256(body).hexdigest() != artifact.sha256
    ):
        raise StoreError("invalid_artifact_bytes")
    if artifact.kind in {"original_html", "sanitized_html", "plain_text"}:
        body.decode("utf-8", errors="strict")


def validate_observations(manifest, observations):
    result = tuple(EvidenceObservation.model_validate(value) for value in observations)
    if len({obs.observation_id for obs in result}) != len(result):
        raise StoreError("duplicate_observation")
    links = {(item.evidence_id, item.locator) for item in manifest.items}
    if len({(obs.evidence_id, obs.locator) for obs in result}) != len(result):
        raise StoreError("duplicate_observation")
    for obs in result:
        if (
            (obs.evidence_id, obs.locator) not in links
            or obs.observation_id != retrieval_observation_id(obs)
            or obs.retrieval_id != manifest.retrieval.retrieval_id
            or obs.evidence_kind != "hybrid"
            or obs.evidence_schema_version != "2.0"
            or obs.adapter_version != manifest.adapter_version
            or obs.source_policy_id != manifest.policy.policy_id
            or obs.source_policy_version != manifest.policy.policy_version
        ):
            raise StoreError("invalid_observation")
    return result


def available_assertion(artifact, policy, at):
    return ArtifactAvailability(
        kind="artifact_availability",
        artifact_id=artifact.artifact_id,
        policy=artifact.policy,
        state="available",
        recorded_at=at,
        retention_until=retention_deadline(policy, artifact),
    )
