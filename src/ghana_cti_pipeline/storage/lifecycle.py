"""Explicit offline lifecycle operations; no scheduler, source access or production paths."""

import hashlib
import os
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from uuid import UUID, uuid4

from ghana_cti_pipeline.core.evidence_values import PolicyReference
from ghana_cti_pipeline.core.source_policy import SourcePolicy
from ghana_cti_pipeline.storage.capacity import (
    DIRECTORIES,
    LIVE_CAP,
    MARGIN,
    Workspace,
    checked,
    fsync_directory,
    fsync_file,
    private_file,
)
from ghana_cti_pipeline.storage.purge import delete_policies, expired
from ghana_cti_pipeline.storage.records import StoreError, serialized
from ghana_cti_pipeline.storage.rights_ledger import ZERO, LedgerAuthority, RightsLedger, policy_key
from ghana_cti_pipeline.storage.sqlite import SQLiteEvidenceStore, safe_errors
from ghana_cti_pipeline.storage.sqlite_schema import SCHEMA_VERSION
from ghana_cti_pipeline.storage.validation import time_key, timestamp
from ghana_cti_pipeline.storage.verification import policies, verify_store


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(MARGIN):
            digest.update(block)
    return digest.hexdigest()


class _ManagedStore(SQLiteEvidenceStore):
    def __init__(self, path, workspace, ledger):
        self.workspace = workspace
        self.ledger = ledger
        self.path = path
        self._cost = 0
        self._initializing = True
        super().__init__(path)
        self._initializing = False
        self._db.execute("PRAGMA temp_store=MEMORY")

    @contextmanager
    def _transaction(self):
        if not self._initializing:
            self.workspace.reserve(self._cost)
            self.workspace.constrain(self._db, self.path)
        self._db.execute("BEGIN IMMEDIATE")
        try:
            yield
            if self.workspace.report().used_bytes > self.workspace.cap_bytes:
                raise StoreError("capacity_pause")
            self._db.execute("COMMIT")
        except BaseException:
            # SQLITE_FULL/IOERR may already have rolled the transaction back.
            if self._db.in_transaction:
                self._db.execute("ROLLBACK")
            raise

    @safe_errors
    def set_policy(self, policy):
        policy = SourcePolicy.model_validate(policy)
        if policy_key(policy.reference) in self.ledger.blocked():
            raise StoreError("retired_policy")
        self._cost = 4 * len(serialized(policy).encode())
        try:
            super().set_policy(policy)
        finally:
            self._cost = 0

    @safe_errors
    def commit_batch(self, manifest, evidence, artifact_bytes, observations, *, at):
        if policy_key(manifest.policy) in self.ledger.blocked():
            raise StoreError("retired_policy")
        evidence, observations = tuple(evidence), tuple(observations)
        self._cost = 4 * (
            sum(len(body) for body in artifact_bytes.values())
            + len(serialized(manifest).encode())
            + sum(len(serialized(record).encode()) for record in (*evidence, *observations))
        )
        try:
            super().commit_batch(manifest, evidence, artifact_bytes, observations, at=at)
        finally:
            self._cost = 0


class LifecycleStore:
    """Owned private workspace. Only synthetic temporary use is currently approved."""

    @safe_errors
    def __init__(self, root: Path, authority: LedgerAuthority, *, at, cap_bytes=LIVE_CAP):
        self.workspace = Workspace(root, cap_bytes)
        self.root = self.workspace.root
        self.authority = LedgerAuthority.model_validate(authority)
        self._time(at)
        with self.workspace.locked():
            existing = {p.name for p in self.root.iterdir()} - {".lock"}
            create = not existing
            if create:
                self.workspace.reserve()
                for name in DIRECTORIES:
                    (self.root / name).mkdir(mode=0o700)
            elif not DIRECTORIES <= existing or "rights.sqlite" not in existing:
                raise StoreError("incomplete_workspace")
            ledger = RightsLedger(self.root / "rights.sqlite", self.authority, create=create)
            try:
                if create:
                    with SQLiteEvidenceStore(self.root / "live.sqlite"):
                        pass
                if create:
                    self.workspace.reserve()
            finally:
                ledger.close()
            fsync_directory(self.root)

    def _time(self, at):
        at = timestamp(at)
        if at >= self.authority.retain_until:
            raise StoreError("ledger_authority_expired")
        return at

    @contextmanager
    def _operation(self, at, *, maintenance=False):
        try:
            at = self._time(at)
            with self.workspace.locked():
                ledger = RightsLedger(self.root / "rights.sqlite", self.authority)
                try:
                    if not maintenance and (
                        ledger.pending() or any((self.root / "staging").iterdir())
                    ):
                        raise StoreError("maintenance_required")
                    yield ledger, at
                finally:
                    ledger.close()
        except StoreError:
            raise
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError):
            raise StoreError("lifecycle_error") from None

    @contextmanager
    def _open(self, ledger):
        path = self.root / "live.sqlite"
        if not path.exists():
            raise StoreError("missing_live_database")
        with _ManagedStore(path, self.workspace, ledger) as store:
            yield store

    def _require_current(self, store, ledger, at):
        blocked = ledger.blocked()
        if any(
            expired(p, at) or policy_key(p.reference) in blocked for p in policies(store).values()
        ):
            raise StoreError("maintenance_required")
        registered = {
            r["value"]["key"] for r in ledger.events() if r["value"]["action"] == "backup"
        }
        if any(p.stem not in registered for p in (self.root / "backups").iterdir()):
            raise StoreError("maintenance_required")
        events = [r["value"] for r in ledger.events()]
        retired = {v["key"] for v in events if v["action"] == "retire"}
        for event in events:
            if (
                event["action"] == "backup"
                and (self.root / "backups" / f"{event['key']}.sqlite").exists()
            ):
                if event["key"] in retired or time_key(at) >= event["detail"]["retain_until"]:
                    raise StoreError("maintenance_required")

    @contextmanager
    def session(self, *, at):
        """Yield the M1-03 API under lock, rights and capacity guards; close on exit."""
        with self._operation(at) as (ledger, at), self._open(ledger) as store:
            self._require_current(store, ledger, at)
            yield store

    @safe_errors
    def diagnostics(self, *, at):
        with self._operation(at, maintenance=True) as (ledger, _):
            return {
                "capacity": self.workspace.report(),
                "pending": len(ledger.pending()),
                "retired_policies": len(ledger.blocked()),
            }

    def _event(self, ledger, action, key, detail, at):
        self.workspace.reserve(16384)
        self.workspace.constrain(ledger.db, self.root / "rights.sqlite")
        return ledger.append(action, key, detail, at)

    def _copy(self, source, destination):
        self.workspace.reserve(
            (self.root / "live.sqlite").stat().st_size
            if (self.root / "live.sqlite").exists()
            else MARGIN
        )
        private_file(destination)
        with closing(sqlite3.connect(destination, isolation_level=None)) as target:
            target.execute("PRAGMA synchronous=FULL")

            def progress(status, remaining, total):
                if status not in {sqlite3.SQLITE_OK, sqlite3.SQLITE_DONE}:
                    raise StoreError("backup_busy")
                if self.workspace.report().used_bytes > self.workspace.cap_bytes:
                    raise StoreError("capacity_pause")

            source.backup(target, pages=128, progress=progress, sleep=0.0)
        fsync_file(destination)

    @safe_errors
    def backup(self, *, at):
        with self._operation(at) as (ledger, at), self._open(ledger) as store:
            self._require_current(store, ledger, at)
            for policy in policies(store).values():
                if (
                    "backup" not in policy.permitted_processing
                    or at >= policy.retention.backups
                    or policy.basis_status != "documented"
                    or not policy.effective_at <= at < policy.expires_at
                    or policy.reviewed_at is None
                    or policy.reviewed_at > at
                ):
                    raise StoreError("backup_policy_denied")
            with store._snapshot():
                verify_store(store, at=at)
                events = ledger.events()
                anchor = [events[-1]["sequence"], events[-1]["digest"]] if events else [0, ZERO]
                backup_id = str(uuid4())
                stage = self.root / "staging" / f"{backup_id}.sqlite"
                self._copy(store._db, stage)
            with SQLiteEvidenceStore(stage) as candidate:
                verify_store(candidate, at=at)
            destination = self.root / "backups" / stage.name
            os.replace(stage, destination)
            fsync_directory(destination.parent)
            fsync_directory(stage.parent)
            self._event(
                ledger,
                "backup",
                backup_id,
                {
                    "sha256": file_digest(destination),
                    "anchor": anchor,
                    "retain_until": time_key(
                        min(
                            [p.retention.backups for p in policies(store).values()]
                            + [self.authority.retain_until]
                        )
                    ),
                },
                at,
            )
            return UUID(backup_id)

    def _backup_record(self, ledger, backup_id, at):
        key = str(UUID(str(backup_id)))
        events = ledger.events()
        records = [
            r for r in events if r["value"]["action"] == "backup" and r["value"]["key"] == key
        ]
        if len(records) != 1 or any(
            r["value"]["action"] == "retire" and r["value"]["key"] == key for r in events
        ):
            raise StoreError("unavailable_backup")
        value = records[0]["value"]
        if time_key(at) >= value["detail"]["retain_until"]:
            raise StoreError("backup_expired")
        sequence, digest = value["detail"]["anchor"]
        if (sequence == 0 and digest != ZERO) or (
            sequence and (sequence > len(events) or events[sequence - 1]["digest"] != digest)
        ):
            raise StoreError("backup_ledger_mismatch")
        path = self.root / "backups" / f"{key}.sqlite"
        checked(path)
        if file_digest(path) != value["detail"]["sha256"]:
            raise StoreError("corrupt_backup")
        return path

    def _compact(self, path):
        self.workspace.reserve(path.stat().st_size)
        target = self.root / "staging" / f"{uuid4()}.sqlite"
        # VACUUM INTO requires a nonexistent or empty file; reserve it privately first.
        private_file(target)
        with closing(sqlite3.connect(path, isolation_level=None)) as db:
            db.execute("PRAGMA temp_store=MEMORY")
            # Let SQLite finish recovery and retire any cold journal itself.
            db.execute("BEGIN EXCLUSIVE")
            db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            db.execute("COMMIT")
            db.execute("VACUUM INTO ?", (str(target),))
        with SQLiteEvidenceStore(target) as candidate:
            verify_store(candidate)
        fsync_file(target)
        for suffix in ("-journal", "-wal", "-shm"):
            if Path(str(path) + suffix).exists():
                raise StoreError("remaining_sidecar")
        os.replace(target, path)
        fsync_directory(path.parent)
        fsync_directory(target.parent)

    @safe_errors
    def restore(self, backup_id, *, at):
        with self._operation(at) as (ledger, at):
            source = self._backup_record(ledger, backup_id, at)
            self.workspace.reserve(2 * source.stat().st_size)
            stage = self.root / "staging" / f"{uuid4()}.sqlite"
            with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as db:
                self._copy(db, stage)
            with SQLiteEvidenceStore(stage) as candidate:
                verify_store(candidate)
                blocked = ledger.blocked() | {
                    policy_key(p.reference) for p in policies(candidate).values() if expired(p, at)
                }
                with candidate._transaction():
                    candidate._db.execute("PRAGMA secure_delete=ON")
                    delete_policies(candidate, blocked)
                    # An isolated candidate never silently restores operational selectors.
                    candidate._db.execute("DELETE FROM checkpoints")
                    candidate._db.execute("DELETE FROM current_policies")
                verify_store(candidate, at=at)
            self._compact(stage)
            destination = self.root / "restores" / stage.name
            os.replace(stage, destination)
            fsync_directory(destination.parent)
            fsync_directory(stage.parent)
            return destination

    def _retire_copies(self, ledger, at):
        for directory in ("backups", "restores", "staging"):
            for path in (self.root / directory).iterdir():
                checked(path)
                if directory == "backups" and path.name.endswith(".sqlite"):
                    self._event(ledger, "retire", path.stem, {}, at)
                path.unlink()
            fsync_directory(self.root / directory)

    @safe_errors
    def purge(self, *, at, revoke=()):
        """Manual offline expiry/revocation, managed-copy retirement and compaction."""
        revoke = tuple(PolicyReference.model_validate(reference) for reference in revoke)
        with self._operation(at, maintenance=True) as (ledger, at):
            pending = ledger.pending()
            operation = pending[0] if pending else str(uuid4())
            if not pending:
                self._event(ledger, "pending", operation, {}, at)
            for reference in revoke:
                self._event(ledger, "revoke", policy_key(reference), {}, at)
            with self._open(ledger) as store:
                for policy in policies(store).values():
                    if expired(policy, at):
                        self._event(ledger, "expire", policy_key(policy.reference), {}, at)
            # Conservatively retire every managed copy, including interrupted/unregistered ones.
            self._retire_copies(ledger, at)
            with self._open(ledger) as store:
                with store._transaction():
                    store._db.execute("PRAGMA secure_delete=ON")
                    removed = delete_policies(store, ledger.blocked())
                verify_store(store, at=at)
            self._compact(self.root / "live.sqlite")
            fsync_file(self.root / "live.sqlite")
            for key in ledger.pending():
                self._event(ledger, "complete", key, {}, at)
            return {"policies_removed": removed, "physical_erasure_verified": False}
