"""Offline transactional evidence store. No default paths, source access or jobs."""

import os
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter

from ghana_cti_pipeline.core.artifacts import ArtifactAvailability, ArtifactReference
from ghana_cti_pipeline.core.digests import canonical_json
from ghana_cti_pipeline.core.evidence import EvidenceRevisionV2
from ghana_cti_pipeline.core.identities import (
    derived_representation_id,
    evidence_association_id,
    source_revision_projection,
    validate_manifest_evidence,
)
from ghana_cti_pipeline.core.processing import ProcessingManifest
from ghana_cti_pipeline.core.retrieval import (
    EvidenceObservation,
    NotModifiedResponse,
    RetrievalFailure,
    RetrievalOutcome,
)
from ghana_cti_pipeline.core.source_policy import SourcePolicy
from ghana_cti_pipeline.storage.records import (
    CheckpointContext,
    StoredCheckpoint,
    StoreError,
    serialized,
)
from ghana_cti_pipeline.storage.sqlite_schema import APPLICATION_ID, DDL, SCHEMA_VERSION, TABLES
from ghana_cti_pipeline.storage.validation import (
    available_assertion,
    conditionals_supported,
    no_store,
    retention_deadline,
    time_key,
    timestamp,
    validate_bytes,
    validate_observations,
    validate_policy,
)

_evidence = TypeAdapter(EvidenceRevisionV2)
_artifact = TypeAdapter(ArtifactReference)
_retrieval = TypeAdapter(RetrievalOutcome)


def safe_errors(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except StoreError:
            raise
        except sqlite3.Error:
            raise StoreError("storage_error") from None
        except (ValueError, TypeError, KeyError, OSError):
            raise StoreError("invalid_storage_input") from None

    return wrapped


class SQLiteEvidenceStore:
    @safe_errors
    def __init__(self, path: Path):
        path = Path(path).absolute()
        if path.is_symlink():
            raise StoreError("unsafe_database_path")
        if not path.exists():
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(descriptor)
        if not path.is_file() or path.stat().st_mode & 0o077:
            raise StoreError("unsafe_database_path")
        self._db = sqlite3.connect(path, isolation_level=None, timeout=1.0)
        self._db.row_factory = sqlite3.Row
        try:
            self._db.execute("PRAGMA foreign_keys=ON")
            self._db.execute("PRAGMA trusted_schema=OFF")
            if self._db.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise StoreError("foreign_keys_unavailable")
            with self._transaction():
                tables = {
                    row[0]
                    for row in self._db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                app = self._db.execute("PRAGMA application_id").fetchone()[0]
                version = self._db.execute("PRAGMA user_version").fetchone()[0]
                if not tables and app == version == 0:
                    for statement in DDL:
                        self._db.execute(statement)
                    self._db.execute(f"PRAGMA application_id={APPLICATION_ID}")
                    self._db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
                elif app != APPLICATION_ID or version != SCHEMA_VERSION or tables != TABLES:
                    raise StoreError("unsupported_database_schema")
            if self._db.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
                raise StoreError("unsupported_journal_mode")
            self._db.execute("PRAGMA synchronous=FULL")
        except BaseException:
            self._db.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self._db.close()

    @contextmanager
    def _transaction(self):
        self._db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    @contextmanager
    def _snapshot(self):
        self._db.execute("BEGIN")
        try:
            yield
        finally:
            self._db.execute("ROLLBACK")

    def _row(self, table, keys):
        # Table/column identifiers are internal constants; all input values are bound.
        assert table in TABLES
        where = " AND ".join(f"{key}=?" for key in keys)
        return self._db.execute(
            f"SELECT * FROM {table} WHERE {where}", tuple(keys.values())
        ).fetchone()

    def _immutable(self, table, keys, values, *, write=True):
        expected = keys | values
        row = self._row(table, keys)
        if row is not None:
            if dict(row) != expected:
                raise StoreError("immutable_conflict")
        elif not write:
            raise StoreError("missing_backing")
        else:
            columns = ",".join(expected)
            placeholders = ",".join("?" for _ in expected)
            self._db.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(expected.values()),
            )

    def _receipt(self, receipt, *, write=True):
        self._immutable(
            "retrievals",
            {"id": str(receipt.retrieval_id)},
            {
                "source_id": receipt.source_id,
                "kind": receipt.kind,
                "representation_id": str(receipt.representation_retrieval_id)
                if isinstance(receipt, NotModifiedResponse)
                else None,
                "payload": serialized(receipt),
            },
            write=write,
        )

    def _load_receipt(self, retrieval_id):
        row = self._row("retrievals", {"id": str(retrieval_id)})
        if row is None:
            raise StoreError("missing_backing")
        record = _retrieval.validate_json(row["payload"])
        if str(record.retrieval_id) != str(retrieval_id):
            raise StoreError("corrupt_backing")
        self._receipt(record, write=False)
        return record

    @safe_errors
    def set_policy(self, policy: SourcePolicy):
        """Select an asserted policy for offline checks, never activate a source."""
        policy = SourcePolicy.model_validate(policy)
        key = serialized(policy.reference)
        with self._transaction():
            self._immutable("policies", {"id": key}, {"payload": serialized(policy)})
            self._db.execute(
                "INSERT INTO current_policies VALUES (?,?) "
                "ON CONFLICT(source_id) DO UPDATE SET policy_id=excluded.policy_id",
                (policy.reference.source_id, key),
            )

    def _policy(self, reference):
        key = serialized(reference)
        selected = self._row("current_policies", {"source_id": reference.source_id})
        row = self._row("policies", {"id": key})
        if row is None or selected is None or selected["policy_id"] != key:
            raise StoreError("policy_denied")
        policy = SourcePolicy.model_validate_json(row["payload"])
        if policy.reference != reference or serialized(policy) != row["payload"]:
            raise StoreError("corrupt_backing")
        return policy

    def _artifact_row(self, artifact, *, write=True):
        self._immutable(
            "artifacts",
            {"id": str(artifact.artifact_id)},
            {
                "policy_id": serialized(artifact.policy),
                "domain": artifact.digest_domain,
                "digest": artifact.sha256,
                "parent_id": str(artifact.parent.artifact_id)
                if artifact.kind != "http_response"
                else None,
                "retrieval_id": str(artifact.retrieval_id)
                if artifact.kind == "http_response"
                else None,
                "payload": serialized(artifact),
            },
            write=write,
        )

    def _availability(self, artifact, policy, at):
        row = self._db.execute(
            "SELECT * FROM availability WHERE artifact_id=? AND recorded_at<=? "
            "ORDER BY recorded_at DESC LIMIT 1",
            (str(artifact.artifact_id), time_key(at)),
        ).fetchone()
        if row is None:
            raise StoreError("missing_backing")
        record = ArtifactAvailability.model_validate_json(row["payload"])
        if (
            record.artifact_id != artifact.artifact_id
            or record.policy != artifact.policy
            or time_key(record.recorded_at) != row["recorded_at"]
            or record.state != "available"
            or record.retention_until != retention_deadline(policy, artifact)
            or at >= record.retention_until
        ):
            raise StoreError("unavailable_backing")

    def _body(self, artifact, policy, at):
        self._artifact_row(artifact, write=False)
        row = self._row("blobs", {"domain": artifact.digest_domain, "digest": artifact.sha256})
        if row is None:
            raise StoreError("missing_backing")
        validate_bytes(artifact, row["body"])
        self._availability(artifact, policy, at)
        return row["body"]

    def _assertion(self, record, *, write=True):
        self._immutable(
            "availability",
            {"artifact_id": str(record.artifact_id), "recorded_at": time_key(record.recorded_at)},
            {"payload": serialized(record)},
            write=write,
        )

    @safe_errors
    def record_availability(self, record: ArtifactAvailability, *, at):
        record = ArtifactAvailability.model_validate(record)
        at = timestamp(at)
        with self._transaction():
            row = self._row("artifacts", {"id": str(record.artifact_id)})
            if row is None:
                raise StoreError("missing_backing")
            artifact = _artifact.validate_json(row["payload"])
            if artifact.artifact_id != record.artifact_id:
                raise StoreError("corrupt_backing")
            self._artifact_row(artifact, write=False)
            policy = self._policy(record.policy)
            if (
                record.policy != artifact.policy
                or record.retention_until != retention_deadline(policy, artifact)
                or record.recorded_at > at
            ):
                raise StoreError("invalid_availability")
            self._assertion(record)

    def _edges(self, table, column, key, expected):
        rows = self._db.execute(f"SELECT * FROM {table} WHERE {column}=?", (key,))
        actual = {tuple(row) for row in rows}
        if actual != expected:
            raise StoreError("corrupt_association")

    def _bundle(self, bundle, *, write=True):
        association = str(evidence_association_id(bundle))
        revision = str(bundle.evidence_id)
        self._immutable(
            "revisions",
            {"id": revision},
            {
                "logical_id": str(bundle.logical_item_id),
                "payload": canonical_json(source_revision_projection(bundle)).decode("utf-8"),
            },
            write=write,
        )
        self._immutable(
            "evidence",
            {"id": association},
            {
                "revision_id": revision,
                "policy_id": serialized(bundle.provenance.policy),
                "retrieval_id": str(bundle.provenance.first_acquisition.retrieval_id),
                "payload": serialized(bundle),
            },
            write=write,
        )
        roles = (
            ("response", "entry")
            if bundle.mode == "catalog_entry"
            else ("response", "original", "sanitized", "plain_text")
        )
        parent = None
        for role in roles:
            artifact = getattr(bundle, role)
            self._immutable(
                "evidence_artifacts",
                {"evidence_id": association, "role": role},
                {"artifact_id": str(artifact.artifact_id)},
                write=write,
            )
            if role in {"sanitized", "plain_text"}:
                derived = str(derived_representation_id(bundle, artifact.kind))
                binding = {
                    "kind": artifact.kind,
                    "domain": artifact.digest_domain,
                    "sha256": artifact.sha256,
                    "transformation": artifact.transformation.model_dump(mode="json"),
                }
                self._immutable(
                    "derivations",
                    {"id": derived},
                    {
                        "revision_id": revision,
                        "parent_id": parent,
                        "payload": canonical_json(binding).decode("utf-8"),
                    },
                    write=write,
                )
                self._immutable(
                    "evidence_derivations",
                    {"evidence_id": association, "role": role},
                    {"derivation_id": derived},
                    write=write,
                )
                parent = derived
        if not write:
            self._edges(
                "evidence_artifacts",
                "evidence_id",
                association,
                {(association, role, str(getattr(bundle, role).artifact_id)) for role in roles},
            )
            self._edges(
                "evidence_derivations",
                "evidence_id",
                association,
                {
                    (
                        association,
                        role,
                        str(derived_representation_id(bundle, getattr(bundle, role).kind)),
                    )
                    for role in roles
                    if role in {"sanitized", "plain_text"}
                },
            )
        return association

    def _manifest(self, manifest, evidence, *, write=True):
        key = str(manifest.manifest_id)
        self._immutable(
            "manifests",
            {"id": key},
            {
                "retrieval_id": str(manifest.retrieval.retrieval_id),
                "policy_id": serialized(manifest.policy),
                "payload": serialized(manifest),
            },
            write=write,
        )
        for bundle in evidence:
            association = self._bundle(bundle, write=write)
            self._immutable(
                "manifest_evidence",
                {"manifest_id": key, "revision_id": str(bundle.evidence_id)},
                {"evidence_id": association},
                write=write,
            )

        if not write:
            self._edges(
                "manifest_artifacts",
                "manifest_id",
                key,
                {(key, str(a.artifact_id)) for a in (manifest.response, *manifest.artifacts)},
            )
            self._edges(
                "manifest_evidence",
                "manifest_id",
                key,
                {(key, str(b.evidence_id), str(evidence_association_id(b))) for b in evidence},
            )
        for artifact in (manifest.response, *manifest.artifacts):
            self._immutable(
                "manifest_artifacts",
                {"manifest_id": key, "artifact_id": str(artifact.artifact_id)},
                {},
                write=write,
            )

    def _observation(self, observation, source_id, *, write=True):
        policy = {
            "schema_version": "1.0",
            "source_id": source_id,
            "policy_id": observation.source_policy_id,
            "policy_version": observation.source_policy_version,
        }
        self._immutable(
            "observations",
            {"id": str(observation.observation_id)},
            {
                "retrieval_id": str(observation.retrieval_id),
                "revision_id": str(observation.evidence_id),
                "locator": observation.locator,
                "policy_id": canonical_json(policy).decode("utf-8"),
                "payload": serialized(observation),
            },
            write=write,
        )

    def _observed(self, manifest, at):
        for item in manifest.items:
            rows = self._db.execute(
                "SELECT * FROM observations WHERE retrieval_id=? AND revision_id=? AND locator=?",
                (str(manifest.retrieval.retrieval_id), str(item.evidence_id), item.locator),
            ).fetchall()
            if not rows:
                raise StoreError("missing_observation")
            for row in rows:
                obs = EvidenceObservation.model_validate_json(row["payload"])
                if str(obs.observation_id) != row["id"]:
                    raise StoreError("corrupt_backing")
                validate_observations(manifest, (obs,))
                self._observation(obs, manifest.policy.source_id, write=False)
                policy_row = self._row("policies", {"id": row["policy_id"]})
                if policy_row is None:
                    raise StoreError("missing_backing")
                policy = SourcePolicy.model_validate_json(policy_row["payload"])
                if at >= policy.retention.audit:
                    raise StoreError("unavailable_backing")

    def _backing(self, manifest_id, at):
        row = self._row("manifests", {"id": str(manifest_id)})
        if row is None:
            raise StoreError("missing_backing")
        manifest = ProcessingManifest.model_validate_json(row["payload"])
        if str(manifest.manifest_id) != str(manifest_id) or manifest.completeness != "complete":
            raise StoreError("incomplete_backing")
        policy = self._policy(manifest.policy)
        validate_policy(policy, manifest, at)
        evidence = []
        for edge in self._db.execute(
            "SELECT evidence_id FROM manifest_evidence WHERE manifest_id=?", (str(manifest_id),)
        ):
            bundle = self._row("evidence", {"id": edge[0]})
            if bundle is None:
                raise StoreError("missing_backing")
            evidence.append(_evidence.validate_json(bundle["payload"]))
        validate_manifest_evidence(manifest, tuple(evidence))
        self._receipt(manifest.retrieval, write=False)
        self._manifest(manifest, tuple(evidence), write=False)
        self._observed(manifest, at)
        for artifact in (manifest.response, *manifest.artifacts):
            self._body(artifact, policy, at)
        return manifest

    def _checkpoint(self, context):
        row = self._row("checkpoints", {"selector": context.selector()})
        if row is None:
            return None
        checkpoint = StoredCheckpoint.model_validate_json(row["payload"])
        if (
            checkpoint.context != context
            or str(checkpoint.manifest_id) != row["manifest_id"]
            or str(checkpoint.last_retrieval_id) != row["last_retrieval_id"]
        ):
            raise StoreError("checkpoint_context_mismatch")
        return checkpoint

    def _save_checkpoint(self, checkpoint):
        self._db.execute(
            "INSERT INTO checkpoints VALUES (?,?,?,?) ON CONFLICT(selector) DO UPDATE SET "
            "manifest_id=excluded.manifest_id,last_retrieval_id=excluded.last_retrieval_id,"
            "payload=excluded.payload",
            (
                checkpoint.context.selector(),
                str(checkpoint.manifest_id),
                str(checkpoint.last_retrieval_id),
                serialized(checkpoint),
            ),
        )

    @safe_errors
    def commit_batch(
        self, manifest, evidence, artifact_bytes: Mapping[UUID, bytes], observations, *, at
    ):
        at = timestamp(at)
        manifest = ProcessingManifest.model_validate(manifest)
        evidence = tuple(_evidence.validate_python(record) for record in evidence)
        validate_manifest_evidence(manifest, evidence)
        observations = validate_observations(manifest, observations)
        artifacts = (manifest.response, *manifest.artifacts)
        if manifest.completeness != "complete" or manifest.retrieval.ended_at > at:
            raise StoreError("incomplete_batch")
        if no_store(manifest.retrieval):
            raise StoreError("cache_policy_denied")
        if set(artifact_bytes) != {a.artifact_id for a in artifacts}:
            raise StoreError("artifact_set_mismatch")
        for artifact in artifacts:
            validate_bytes(artifact, artifact_bytes[artifact.artifact_id])
        context = CheckpointContext.from_manifest(manifest)
        with self._transaction():
            policy = self._policy(manifest.policy)
            validate_policy(policy, manifest, at)
            if self._row("manifests", {"id": str(manifest.manifest_id)}) is not None:
                self._manifest(manifest, evidence, write=False)
                self._backing(manifest.manifest_id, at)
                for observation in observations:
                    self._observation(observation, manifest.policy.source_id, write=False)
                return
            is_new = self._row("retrievals", {"id": str(manifest.retrieval.retrieval_id)}) is None
            if is_new and len(observations) != len(manifest.items):
                raise StoreError("missing_observation")
            self._receipt(manifest.retrieval)
            if not is_new:
                committed = self._db.execute(
                    "SELECT id FROM manifests WHERE retrieval_id=?",
                    (str(manifest.retrieval.retrieval_id),),
                ).fetchall()
                if not committed:
                    raise StoreError("missing_backing")
                for row in committed:
                    self._backing(row["id"], at)
                for observation in observations:
                    self._observation(observation, manifest.policy.source_id, write=False)
            # Sort only insertion order, never the immutable manifest's arrays.
            order = {
                "http_response": 0,
                "original_html": 1,
                "catalog_entry": 1,
                "sanitized_html": 2,
                "plain_text": 3,
            }
            for artifact in sorted(artifacts, key=lambda a: order[a.kind]):
                existing = self._row("artifacts", {"id": str(artifact.artifact_id)})
                if existing is not None:
                    self._body(artifact, policy, at)  # Never resurrect missing/deleted backing.
                self._immutable(
                    "blobs",
                    {"domain": artifact.digest_domain, "digest": artifact.sha256},
                    {"body": artifact_bytes[artifact.artifact_id]},
                )
                self._artifact_row(artifact)
                if existing is None:
                    self._assertion(available_assertion(artifact, policy, at))
            self._manifest(manifest, evidence)
            for observation in observations:
                self._observation(observation, manifest.policy.source_id)
            self._observed(manifest, at)
            previous_row = self._row("checkpoints", {"selector": context.selector()})
            previous = (
                StoredCheckpoint.model_validate_json(previous_row["payload"])
                if previous_row
                else None
            )
            receipt = manifest.retrieval
            checkpoint = StoredCheckpoint(
                context=context,
                manifest_id=manifest.manifest_id,
                representation_retrieval_id=receipt.retrieval_id,
                last_retrieval_id=receipt.retrieval_id,
                last_checked_at=receipt.ended_at,
                etag=receipt.returned_etag,
                last_modified=receipt.returned_last_modified,
            )
            if previous and previous.representation_retrieval_id == receipt.retrieval_id:
                checkpoint = checkpoint.model_copy(
                    update={
                        "last_retrieval_id": previous.last_retrieval_id,
                        "last_checked_at": previous.last_checked_at,
                        "etag": previous.etag,
                        "last_modified": previous.last_modified,
                    }
                )
            elif previous and previous.last_checked_at > receipt.ended_at:
                raise StoreError("stale_batch")
            self._save_checkpoint(checkpoint)

    def _chain_values(self, retrieval_id, expected_context, anchor):
        checks = []
        seen = set()
        key = retrieval_id
        while key != anchor.retrieval_id:
            if key in seen:
                raise StoreError("corrupt_check_chain")
            seen.add(key)
            receipt = self._load_receipt(key)
            row = self._row("checks", {"retrieval_id": str(key)})
            if row is None or not isinstance(receipt, NotModifiedResponse):
                raise StoreError("missing_check_backing")
            context = CheckpointContext.model_validate_json(row["context"])
            if context.selector() != expected_context.selector():
                raise StoreError("checkpoint_context_mismatch")
            manifest = self._row("manifests", {"id": row["manifest_id"]})
            if manifest is None or manifest["retrieval_id"] != str(anchor.retrieval_id):
                raise StoreError("missing_check_backing")
            checks.append(receipt)
            key = UUID(row["previous_id"])
        etag, modified, checked = (
            anchor.returned_etag,
            anchor.returned_last_modified,
            anchor.ended_at,
        )
        for receipt in reversed(checks):
            self._validate_304(receipt, anchor, etag, modified, checked)
            etag = receipt.returned_etag if receipt.returned_etag is not None else etag
            modified = (
                receipt.returned_last_modified
                if receipt.returned_last_modified is not None
                else modified
            )
            checked = receipt.ended_at
        return etag, modified, checked

    @staticmethod
    def _validate_304(receipt, anchor, etag, modified, checked):
        if (
            receipt.representation_retrieval_id != anchor.retrieval_id
            or receipt.source_id != anchor.source_id
            or receipt.requested_url != anchor.requested_url
            or receipt.final_url != anchor.final_url
            or receipt.redirect_urls != anchor.redirect_urls
            or receipt.started_at < checked
            or (receipt.sent_etag is not None and receipt.sent_etag != etag)
            or (receipt.sent_last_modified is not None and receipt.sent_last_modified != modified)
            or not conditionals_supported(receipt)
        ):
            raise StoreError("invalid_304")

    def _eligible(self, context, at):
        checkpoint = self._checkpoint(context)
        if checkpoint is None:
            raise StoreError("missing_checkpoint")
        manifest = self._backing(checkpoint.manifest_id, at)
        if (
            context != CheckpointContext.from_manifest(manifest)
            or checkpoint.representation_retrieval_id != manifest.retrieval.retrieval_id
            or checkpoint.last_checked_at > at
            or not conditionals_supported(manifest.retrieval)
            or (checkpoint.etag is None and checkpoint.last_modified is None)
        ):
            raise StoreError("ineligible_checkpoint")
        if (checkpoint.etag, checkpoint.last_modified, checkpoint.last_checked_at) != (
            self._chain_values(checkpoint.last_retrieval_id, context, manifest.retrieval)
        ):
            raise StoreError("corrupt_checkpoint")
        return checkpoint, manifest

    @safe_errors
    def get_checkpoint(self, context: CheckpointContext, *, at) -> StoredCheckpoint | None:
        context = CheckpointContext.model_validate(context)
        at = timestamp(at)
        try:
            # One read snapshot across all backing checks.
            with self._snapshot():
                return self._eligible(context, at)[0]
        except (ValueError, TypeError, KeyError):
            return None

    @safe_errors
    def record_not_modified(self, receipt: NotModifiedResponse, context: CheckpointContext, *, at):
        receipt = NotModifiedResponse.model_validate(receipt)
        context = CheckpointContext.model_validate(context)
        at = timestamp(at)
        if receipt.ended_at > at:
            raise StoreError("future_retrieval")
        with self._transaction():
            prior = self._row("retrievals", {"id": str(receipt.retrieval_id)})
            if prior is not None:
                self._receipt(receipt, write=False)
                check = self._row("checks", {"retrieval_id": str(receipt.retrieval_id)})
                if check is None or check["context"] != serialized(context):
                    raise StoreError("immutable_conflict")
                manifest = self._backing(check["manifest_id"], at)
                if context != CheckpointContext.from_manifest(manifest):
                    raise StoreError("checkpoint_context_mismatch")
                self._chain_values(receipt.retrieval_id, context, manifest.retrieval)
                return
            checkpoint, manifest = self._eligible(context, at)
            self._validate_304(
                receipt,
                manifest.retrieval,
                checkpoint.etag,
                checkpoint.last_modified,
                checkpoint.last_checked_at,
            )
            self._receipt(receipt)
            self._immutable(
                "checks",
                {"retrieval_id": str(receipt.retrieval_id)},
                {
                    "previous_id": str(checkpoint.last_retrieval_id),
                    "manifest_id": str(checkpoint.manifest_id),
                    "context": serialized(context),
                },
            )
            self._save_checkpoint(
                checkpoint.model_copy(
                    update={
                        "last_retrieval_id": receipt.retrieval_id,
                        "last_checked_at": receipt.ended_at,
                        "etag": receipt.returned_etag
                        if receipt.returned_etag is not None
                        else checkpoint.etag,
                        "last_modified": receipt.returned_last_modified
                        if receipt.returned_last_modified is not None
                        else checkpoint.last_modified,
                    }
                )
            )

    @safe_errors
    def record_failure(self, receipt: RetrievalFailure):
        receipt = RetrievalFailure.model_validate(receipt)
        with self._transaction():
            self._receipt(receipt)

    @safe_errors
    def get_artifact(self, artifact_id: UUID, *, at) -> bytes | None:
        at = timestamp(at)
        with self._snapshot():
            return self._get_artifact(artifact_id, at)

    def _get_artifact(self, artifact_id, at):
        row = self._row("artifacts", {"id": str(artifact_id)})
        if row is None:
            return None
        artifact = _artifact.validate_json(row["payload"])
        if artifact.artifact_id != artifact_id:
            raise StoreError("corrupt_backing")
        policy = self._policy(artifact.policy)
        if (
            policy.basis_status != "documented"
            or not policy.effective_at <= at < policy.expires_at
            or artifact.kind not in policy.permitted_artifacts
            or not {"retain", "internal_use"} <= set(policy.permitted_processing)
            or at >= retention_deadline(policy, artifact)
        ):
            raise StoreError("policy_denied")
        return self._body(artifact, policy, at)

    @safe_errors
    def get_evidence(self, association_id: UUID):
        """Internal metadata read; no body availability or publication assertion."""
        row = self._row("evidence", {"id": str(association_id)})
        return None if row is None else _evidence.validate_json(row["payload"])

    @safe_errors
    def get_retrieval(self, retrieval_id: UUID):
        if self._row("retrievals", {"id": str(retrieval_id)}) is None:
            return None
        return self._load_receipt(retrieval_id)
