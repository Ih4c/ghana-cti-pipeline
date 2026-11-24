"""Full offline database verification, independent of live checkpoint eligibility."""

from uuid import UUID

from pydantic import TypeAdapter

from ghana_cti_pipeline.core.artifacts import ArtifactAvailability, ArtifactReference
from ghana_cti_pipeline.core.evidence import EvidenceRevisionV2
from ghana_cti_pipeline.core.identities import (
    artifact_association_id,
    evidence_association_id,
    validate_manifest_evidence,
)
from ghana_cti_pipeline.core.processing import ProcessingManifest
from ghana_cti_pipeline.core.retrieval import (
    EvidenceObservation,
    NotModifiedResponse,
    RetrievalFailure,
)
from ghana_cti_pipeline.core.source_policy import SourcePolicy
from ghana_cti_pipeline.storage.records import (
    CheckpointContext,
    StoredCheckpoint,
    StoreError,
    serialized,
)
from ghana_cti_pipeline.storage.validation import (
    validate_bytes,
    validate_observations,
    validate_policy,
)

_artifact = TypeAdapter(ArtifactReference)
_evidence = TypeAdapter(EvidenceRevisionV2)


def policies(store):
    result = {}
    for row in store._db.execute("SELECT * FROM policies"):
        policy = SourcePolicy.model_validate_json(row["payload"])
        if serialized(policy.reference) != row["id"] or serialized(policy) != row["payload"]:
            raise StoreError("corrupt_policy")
        result[row["id"]] = policy
    return result


def verify_store(store, *, at=None):
    """Validate every retained graph, including historical/non-selected policies."""
    db = store._db
    if [r[0] for r in db.execute("PRAGMA integrity_check")] != ["ok"]:
        raise StoreError("database_integrity")
    if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise StoreError("foreign_key_integrity")
    policy_map = policies(store)
    for row in db.execute("SELECT * FROM current_policies"):
        if policy_map[row["policy_id"]].reference.source_id != row["source_id"]:
            raise StoreError("corrupt_policy_selector")
    covered_observations = set()
    manifest_map = {}
    for row in db.execute("SELECT * FROM manifests"):
        manifest = ProcessingManifest.model_validate_json(row["payload"])
        if str(manifest.manifest_id) != row["id"] or manifest.completeness != "complete":
            raise StoreError("incomplete_manifest")
        bundles = []
        for edge in db.execute("SELECT * FROM manifest_evidence WHERE manifest_id=?", (row["id"],)):
            item = store._row("evidence", {"id": edge["evidence_id"]})
            bundle = _evidence.validate_json(item["payload"])
            if str(evidence_association_id(bundle)) != edge["evidence_id"]:
                raise StoreError("corrupt_association")
            bundles.append(bundle)
        validate_manifest_evidence(manifest, tuple(bundles))
        store._manifest(manifest, tuple(bundles), write=False)
        store._receipt(manifest.retrieval, write=False)
        observations = [
            EvidenceObservation.model_validate_json(r["payload"])
            for r in db.execute(
                "SELECT payload FROM observations WHERE retrieval_id=?",
                (str(manifest.retrieval.retrieval_id),),
            )
        ]
        validate_observations(manifest, observations)
        if len(observations) != len(manifest.items):
            raise StoreError("missing_observation")
        for observation in observations:
            store._observation(observation, manifest.policy.source_id, write=False)
            covered_observations.add(str(observation.observation_id))
        if at is not None:
            policy = policy_map[serialized(manifest.policy)]
            validate_policy(policy, manifest, at)
            for artifact in (manifest.response, *manifest.artifacts):
                store._body(artifact, policy, at)
        manifest_map[row["id"]] = manifest
    for row in db.execute("SELECT * FROM artifacts"):
        artifact = _artifact.validate_json(row["payload"])
        if str(artifact_association_id(artifact)) != row["id"]:
            raise StoreError("corrupt_artifact")
        store._artifact_row(artifact, write=False)
        blob = store._row("blobs", {"domain": artifact.digest_domain, "digest": artifact.sha256})
        validate_bytes(artifact, blob["body"])
    for row in db.execute("SELECT * FROM availability"):
        event = ArtifactAvailability.model_validate_json(row["payload"])
        store._assertion(event, write=False)
        artifact = _artifact.validate_json(
            store._row("artifacts", {"id": row["artifact_id"]})["payload"]
        )
        if event.policy != artifact.policy or str(event.artifact_id) != row["artifact_id"]:
            raise StoreError("corrupt_availability")
    observed = {r[0] for r in db.execute("SELECT id FROM observations")}
    if observed != covered_observations:
        raise StoreError("orphan_observation")
    # Every stored immutable row must belong to the graph, not just the newest manifest.
    for table, projection in (
        ("artifacts", "SELECT artifact_id FROM manifest_artifacts"),
        ("evidence", "SELECT evidence_id FROM manifest_evidence"),
        ("revisions", "SELECT revision_id FROM evidence"),
        ("derivations", "SELECT derivation_id FROM evidence_derivations"),
    ):
        if {r[0] for r in db.execute(f"SELECT id FROM {table}")} != {
            r[0] for r in db.execute(projection)
        }:
            raise StoreError("orphan_backing")
    if {tuple(r) for r in db.execute("SELECT domain,digest FROM blobs")} != {
        tuple(r) for r in db.execute("SELECT domain,digest FROM artifacts")
    }:
        raise StoreError("orphan_blob")
    checked_receipts = set()
    for row in db.execute("SELECT * FROM checks"):
        context = CheckpointContext.model_validate_json(row["context"])
        manifest = manifest_map[row["manifest_id"]]
        if context != CheckpointContext.from_manifest(manifest):
            raise StoreError("corrupt_check_context")
        store._chain_values(UUID(row["retrieval_id"]), context, manifest.retrieval)
        checked_receipts.add(row["retrieval_id"])
    anchors = {str(m.retrieval.retrieval_id) for m in manifest_map.values()}
    for row in db.execute("SELECT id FROM retrievals"):
        receipt = store._load_receipt(UUID(row["id"]))
        if isinstance(receipt, RetrievalFailure):
            continue
        expected = checked_receipts if isinstance(receipt, NotModifiedResponse) else anchors
        if row["id"] not in expected:
            raise StoreError("orphan_retrieval")
    for row in db.execute("SELECT * FROM checkpoints"):
        checkpoint = StoredCheckpoint.model_validate_json(row["payload"])
        if row["selector"] != checkpoint.context.selector():
            raise StoreError("corrupt_checkpoint")
        store._checkpoint(checkpoint.context)
        manifest = manifest_map[str(checkpoint.manifest_id)]
        if (
            checkpoint.context != CheckpointContext.from_manifest(manifest)
            or checkpoint.representation_retrieval_id != manifest.retrieval.retrieval_id
            or (checkpoint.etag, checkpoint.last_modified, checkpoint.last_checked_at)
            != store._chain_values(
                checkpoint.last_retrieval_id, checkpoint.context, manifest.retrieval
            )
        ):
            raise StoreError("corrupt_checkpoint")
    return {
        name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        for name in ("manifests", "evidence", "artifacts", "retrievals", "observations")
    }
