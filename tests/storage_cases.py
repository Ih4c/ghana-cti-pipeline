"""Synthetic descriptors and exact bytes, never collected source material."""

import copy
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter

from ghana_cti_pipeline.core.artifacts import ArtifactReference
from ghana_cti_pipeline.core.digests import canonical_json
from ghana_cti_pipeline.core.evidence import EvidenceRevisionV2
from ghana_cti_pipeline.core.identities import (
    IDENTITY_PROFILE,
    artifact_association_id,
    evidence_metadata_digest,
    logical_item_id,
    processing_manifest_digest,
    processing_manifest_id,
    retrieval_observation_id,
    source_revision_id,
)
from ghana_cti_pipeline.core.processing import ProcessingManifest
from ghana_cti_pipeline.core.retrieval import EvidenceObservation, NotModifiedResponse
from ghana_cti_pipeline.core.source_policy import SourcePolicy
from ghana_cti_pipeline.storage.records import CheckpointContext

NOW = datetime(2026, 1, 15, 12, tzinfo=UTC)
FIXTURE = Path(__file__).parent / "fixtures/evidence_v2.json"


@dataclass(frozen=True)
class Case:
    policy: SourcePolicy
    manifest: ProcessingManifest
    evidence: tuple
    bodies: dict
    observations: tuple

    @property
    def context(self):
        return CheckpointContext.from_manifest(self.manifest)

    def commit(self, store, *, at=NOW, observations=None):
        store.commit_batch(
            self.manifest,
            self.evidence,
            self.bodies,
            self.observations if observations is None else observations,
            at=at,
        )


def case(
    base="microsoft",
    *,
    cycle=0,
    original="<p>synthetic A</p>",
    sanitizer="s1",
    extractor="t1",
    source=None,
    cache_control="max-age=3600",
    vary="Accept-Encoding",
):
    fixtures = json.loads(FIXTURE.read_text("utf-8"))
    data = copy.deepcopy(fixtures[base])
    if source:

        def replace_source(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "source_id":
                        value[key] = source
                    else:
                        replace_source(child)
            elif isinstance(value, list):
                for child in value:
                    replace_source(child)

        replace_source(data)
    provenance = data["provenance"]
    provenance["identity_profile"] = IDENTITY_PROFILE
    receipt = provenance["first_acquisition"]
    receipt.update(
        retrieval_id=str(UUID(int=1000 + cycle)),
        started_at=NOW - timedelta(hours=1) + timedelta(minutes=cycle),
        ended_at=NOW - timedelta(hours=1) + timedelta(minutes=cycle, seconds=1),
        cache_control=cache_control,
        vary=vary,
    )
    content = {"response": f"synthetic response {base}/{cycle}/{original}".encode()}
    if data["mode"] == "feed_full_text":
        content |= {
            "original": original.encode(),
            "sanitized": b"<p>synthetic safe</p>",
            "plain_text": b"synthetic safe",
        }
        data["sanitized"]["transformation"]["implementation_version"] = sanitizer
        data["plain_text"]["transformation"]["implementation_version"] = extractor
    else:
        content["entry"] = canonical_json(data["fields"] | {"syntheticExtension": original})
    digest = sha256(content["response"]).hexdigest()
    receipt["body_metadata"].update(
        decoded_bytes=len(content["response"]),
        transferred_bytes=len(content["response"]),
        content_encoding="identity",
        digest={"digest_state": "computed", "domain": "decoded-http-entity-v1", "sha256": digest},
    )
    data["response"]["retrieval_id"] = receipt["retrieval_id"]
    bodies = {}
    previous = None
    for role, body in content.items():
        artifact = data[role]
        artifact.update(sha256=sha256(body).hexdigest(), byte_count=len(body))
        if previous is not None:
            artifact["parent"] = {
                key: previous[key] for key in ("artifact_id", "kind", "sha256", "digest_domain")
            }
        value = TypeAdapter(ArtifactReference).validate_python(artifact)
        artifact["artifact_id"] = str(artifact_association_id(value))
        bodies[UUID(artifact["artifact_id"])] = body
        previous = artifact
    bundle = TypeAdapter(EvidenceRevisionV2).validate_python(data)
    bundle = bundle.model_copy(
        update={
            "logical_item_id": logical_item_id(provenance["source_id"], provenance["source_key"]),
            "evidence_id": source_revision_id(bundle),
        }
    )
    bundle = bundle.model_copy(update={"metadata_digest": evidence_metadata_digest(bundle)})
    manifest = copy.deepcopy(fixtures["manifest"])
    item = {
        "mode": bundle.mode,
        "evidence_id": bundle.evidence_id,
        "evidence_kind": "hybrid",
        "evidence_schema_version": "2.0",
        "evidence_digest": bundle.metadata_digest,
        "locator": provenance["locator"],
    }
    for role in list(content)[1:]:
        item[role + "_id"] = getattr(bundle, role).artifact_id
    manifest.update(
        mode=bundle.mode,
        policy=bundle.provenance.policy,
        retrieval=bundle.provenance.first_acquisition,
        request_variant_id=provenance["request_variant_id"],
        adapter_version=provenance["adapter_version"],
        parser_version=provenance["parser_version"],
        response=bundle.response,
        artifacts=[getattr(bundle, key) for key in list(content)[1:]],
        items=[item],
        expected_item_count=1,
    )
    manifest = ProcessingManifest.model_validate(manifest)
    manifest = manifest.model_copy(update={"digest": processing_manifest_digest(manifest)})
    manifest = manifest.model_copy(update={"manifest_id": processing_manifest_id(manifest)})
    observation = EvidenceObservation(
        kind="evidence_observation",
        observation_id=UUID(int=0),
        retrieval_id=manifest.retrieval.retrieval_id,
        evidence_id=bundle.evidence_id,
        evidence_kind="hybrid",
        evidence_schema_version="2.0",
        locator=provenance["locator"],
        adapter_version=provenance["adapter_version"],
        source_policy_id=bundle.provenance.policy.policy_id,
        source_policy_version=bundle.provenance.policy.policy_version,
    )
    observation = observation.model_copy(
        update={"observation_id": retrieval_observation_id(observation)}
    )
    policy = copy.deepcopy(fixtures["policy"])
    policy.update(
        reference=bundle.provenance.policy,
        endpoint=receipt["requested_url"],
        mode=bundle.mode,
        basis_status="documented",
        basis_references=["https://example.org/synthetic-permission"],
        reviewed_at="2026-01-01T00:00:00Z",
        effective_at="2026-01-01T00:00:00Z",
        expires_at="2027-01-01T00:00:00Z",
        permitted_artifacts=[getattr(bundle, role).kind for role in content],
        permitted_processing=["retrieve", "retain", "internal_use"]
        + (["sanitize_html", "extract_text"] if bundle.mode == "feed_full_text" else []),
        retention={
            name: "2026-12-31T00:00:00Z"
            for name in (
                "response",
                "original",
                "derived",
                "metadata",
                "digests",
                "audit",
                "backups",
            )
        },
    )
    return Case(SourcePolicy.model_validate(policy), manifest, (bundle,), bodies, (observation,))


def not_modified(example, *, number=0, sent_etag='"synthetic-v1"', returned_etag='"synthetic-v2"'):
    anchor = example.manifest.retrieval
    return NotModifiedResponse(
        kind="not_modified_response",
        retrieval_id=UUID(int=2000 + number),
        representation_retrieval_id=anchor.retrieval_id,
        source_id=anchor.source_id,
        requested_url=anchor.requested_url,
        final_url=anchor.final_url,
        redirect_urls=anchor.redirect_urls,
        status=304,
        started_at=NOW + timedelta(minutes=number * 2 + 1),
        ended_at=NOW + timedelta(minutes=number * 2 + 1, seconds=1),
        sent_etag=sent_etag,
        returned_etag=returned_etag,
    )
