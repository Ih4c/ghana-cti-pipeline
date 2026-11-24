"""Offline lifecycle tests: synthetic evidence, private temporary workspaces, no sources."""

import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from storage_cases import NOW, case

from ghana_cti_pipeline.storage.capacity import LIVE_CAP, MARGIN, Workspace
from ghana_cti_pipeline.storage.lifecycle import LifecycleStore
from ghana_cti_pipeline.storage.records import StoreError
from ghana_cti_pipeline.storage.rights_ledger import LedgerAuthority
from ghana_cti_pipeline.storage.sqlite import SQLiteEvidenceStore
from ghana_cti_pipeline.storage.verification import verify_store


@pytest.fixture(autouse=True)
def deny_dns(monkeypatch):
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("No DNS in offline lifecycle tests")

    monkeypatch.setattr(socket, "getaddrinfo", denied)


@pytest.fixture
def authority():
    return LedgerAuthority(
        basis="https://example.org/synthetic-ledger-basis", retain_until=NOW + timedelta(days=2000)
    )


@pytest.fixture
def manager(tmp_path, authority):
    return LifecycleStore(tmp_path / "private", authority, at=NOW)


def example_with_backup(**kwargs):
    example = case(**kwargs)
    return replace(
        example,
        policy=example.policy.model_copy(
            update={"permitted_processing": (*example.policy.permitted_processing, "backup")}
        ),
    )


def install(manager, example):
    with manager.session(at=NOW) as store:
        store.set_policy(example.policy)
        example.commit(store)


def count(store, table):
    return store._db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_roundtrip_backup_restore_and_existing_store_compatibility(manager):
    example = example_with_backup()
    install(manager, example)
    with manager.session(at=NOW) as store:
        verify_store(store, at=NOW)
        example.commit(store)
        assert store.get_checkpoint(example.context, at=NOW)
    backup = manager.backup(at=NOW)
    # The snapshot must remain unchanged after another live commit.
    with manager.session(at=NOW) as store:
        case(cycle=1, original="<p>synthetic second revision</p>").commit(store)
    candidate = manager.restore(backup, at=NOW)
    with SQLiteEvidenceStore(candidate) as store:
        assert verify_store(store, at=NOW)["manifests"] == 1
        assert store.get_checkpoint(example.context, at=NOW) is None
        assert count(store, "current_policies") == 0
        store.set_policy(example.policy)
        assert (
            store.get_artifact(example.manifest.response.artifact_id, at=NOW)
            == example.bodies[example.manifest.response.artifact_id]
        )
    with manager.session(at=NOW) as store:
        assert count(store, "manifests") == 2
    assert manager.diagnostics(at=NOW)["pending"] == 0


def test_backup_requires_explicit_permission(manager):
    install(manager, case())
    with pytest.raises(StoreError, match="backup_policy_denied"):
        manager.backup(at=NOW)
    assert not list((manager.root / "backups").iterdir())


@pytest.mark.parametrize(
    "group", ["response", "original", "derived", "metadata", "digests", "audit"]
)
def test_expiry_purges_whole_policy_and_all_managed_copies(manager, group):
    example = example_with_backup(original="<p>UNIQUE_SYNTHETIC_PURGE_CANARY_04</p>")
    deadline = NOW + timedelta(minutes=1)
    example = replace(
        example,
        policy=example.policy.model_copy(
            update={"retention": example.policy.retention.model_copy(update={group: deadline})}
        ),
    )
    install(manager, example)
    backup = manager.backup(at=NOW)
    manager.restore(backup, at=NOW)
    with pytest.raises(StoreError, match="maintenance_required"), manager.session(at=deadline):
        pass
    result = manager.purge(at=deadline)
    assert result == {"policies_removed": 1, "physical_erasure_verified": False}
    with manager.session(at=deadline) as store:
        assert verify_store(store, at=deadline)["artifacts"] == 0
        assert store.get_checkpoint(example.context, at=deadline) is None
        with pytest.raises(StoreError, match="retired_policy"):
            store.set_policy(example.policy)
    for path in manager.workspace.inventory():
        assert b"UNIQUE_SYNTHETIC_PURGE_CANARY_04" not in path.read_bytes()
    assert not list((manager.root / "backups").iterdir())
    assert not list((manager.root / "restores").iterdir())
    assert not list((manager.root / "staging").iterdir())
    with pytest.raises(StoreError, match="unavailable_backup"):
        manager.restore(backup, at=deadline)
    assert manager.purge(at=deadline)["policies_removed"] == 0


def test_revocation_preserves_independent_source_and_shared_permitted_bytes(manager):
    first = example_with_backup()
    other = example_with_backup(cycle=1, source="independent-source")
    install(manager, first)
    install(manager, other)
    manager.purge(at=NOW, revoke=(first.policy.reference,))
    with manager.session(at=NOW) as store:
        assert store.get_checkpoint(first.context, at=NOW) is None
        assert store.get_checkpoint(other.context, at=NOW)
        assert verify_store(store, at=NOW)["evidence"] == 1
        assert (
            store.get_artifact(other.evidence[0].original.artifact_id, at=NOW)
            == b"<p>synthetic A</p>"
        )
    # A new policy reference is not silently inferred from an old revoked one.
    with manager.session(at=NOW) as store, pytest.raises(StoreError, match="retired_policy"):
        store.set_policy(first.policy)


def test_restore_applies_current_expiry_before_any_conditional_use(manager):
    example = example_with_backup()
    deadline = NOW + timedelta(minutes=1)
    example = replace(
        example,
        policy=example.policy.model_copy(
            update={"retention": example.policy.retention.model_copy(update={"original": deadline})}
        ),
    )
    install(manager, example)
    backup = manager.backup(at=NOW)
    candidate = manager.restore(backup, at=deadline)
    with SQLiteEvidenceStore(candidate) as store:
        assert verify_store(store)["artifacts"] == 0
        assert count(store, "checkpoints") == 0


def test_retired_backup_cannot_resurrect_content_even_if_file_reappears(manager):
    example = example_with_backup()
    install(manager, example)
    backup = manager.backup(at=NOW)
    path = manager.root / "backups" / f"{backup}.sqlite"
    data = path.read_bytes()
    manager.purge(at=NOW, revoke=(example.policy.reference,))
    path.write_bytes(data)
    path.chmod(0o600)
    with pytest.raises(StoreError, match="unavailable_backup"):
        manager.restore(backup, at=NOW)


def test_failed_compaction_blocks_use_and_is_retryable(manager, monkeypatch):
    example = example_with_backup(original="<p>SYNTHETIC_INTERRUPTED_PURGE</p>")
    install(manager, example)
    manager.backup(at=NOW)

    def interrupted(path):
        raise OSError("synthetic failure; must not escape")

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_compact", interrupted)
        with pytest.raises(StoreError, match="lifecycle_error"):
            manager.purge(at=NOW, revoke=(example.policy.reference,))
    assert manager.diagnostics(at=NOW)["pending"] == 1
    with pytest.raises(StoreError, match="maintenance_required"), manager.session(at=NOW):
        pass
    with pytest.raises(StoreError, match="maintenance_required"):
        manager.backup(at=NOW)
    manager.purge(at=NOW)
    assert manager.diagnostics(at=NOW)["pending"] == 0
    for path in manager.workspace.inventory():
        assert b"SYNTHETIC_INTERRUPTED_PURGE" not in path.read_bytes()


def test_ledger_is_append_only_and_not_restored(manager):
    example = example_with_backup()
    install(manager, example)
    backup = manager.backup(at=NOW)
    with closing(sqlite3.connect(manager.root / "rights.sqlite")) as db:
        with pytest.raises(sqlite3.IntegrityError, match="append_only"):
            db.execute("DELETE FROM events")
        with pytest.raises(sqlite3.IntegrityError, match="append_only"):
            db.execute("UPDATE events SET digest='changed'")
    with manager._operation(NOW, maintenance=True) as (ledger, _):
        before = ledger.events()
    manager.restore(backup, at=NOW)
    with manager._operation(NOW, maintenance=True) as (ledger, _):
        assert ledger.events() == before


@pytest.mark.parametrize("mutation", ["bytes", "schema", "fk", "manifest", "derivation"])
def test_backup_rejects_corruption_before_registration(manager, mutation):
    example = example_with_backup()
    install(manager, example)
    with closing(sqlite3.connect(manager.root / "live.sqlite", isolation_level=None)) as db:
        if mutation == "bytes":
            db.execute("UPDATE blobs SET body=?", (b"synthetic damage",))
        elif mutation == "schema":
            db.execute("PRAGMA user_version=99")
        elif mutation == "fk":
            db.execute("DELETE FROM artifacts")
        else:
            table = "manifests" if mutation == "manifest" else "derivations"
            db.execute(f"UPDATE {table} SET payload='{{}}'")
    with pytest.raises(StoreError):
        manager.backup(at=NOW)
    assert not list((manager.root / "backups").iterdir())


def test_backup_digest_and_missing_ledger_fail_closed(manager, authority):
    install(manager, example_with_backup())
    backup = manager.backup(at=NOW)
    path = manager.root / "backups" / f"{backup}.sqlite"
    with path.open("ab") as stream:
        stream.write(b"synthetic damage")
    with pytest.raises(StoreError, match="corrupt_backup"):
        manager.restore(backup, at=NOW)
    (manager.root / "rights.sqlite").unlink()
    with pytest.raises(StoreError, match="incomplete_workspace"):
        LifecycleStore(manager.root, authority, at=NOW)


def test_capacity_warning_exact_limit_and_all_files_counted(tmp_path):
    workspace = Workspace(tmp_path / "private", cap_bytes=5 * MARGIN)
    (workspace.root / "staging").mkdir(mode=0o700)
    path = workspace.root / "staging" / f"{uuid4()}.sqlite"
    with path.open("wb") as stream:
        stream.truncate(4 * MARGIN)
    path.chmod(0o600)
    report = workspace.report()
    assert report.used_bytes == 4 * MARGIN
    assert report.warning
    workspace.reserve(0)  # Exactly the cap after the fixed margin.
    with pytest.raises(StoreError, match="capacity_pause"):
        workspace.reserve(1)
    for name in ("live.sqlite-wal", "live.sqlite-shm", "live.sqlite-journal"):
        sidecar = workspace.root / name
        sidecar.write_bytes(b"synthetic")
        sidecar.chmod(0o600)
    assert workspace.report().used_bytes == 4 * MARGIN + 27
    with pytest.raises(StoreError, match="invalid_capacity_limit"):
        Workspace(tmp_path / "oversize", LIVE_CAP + 1)


def test_insufficient_space_pauses_before_batch_without_checkpoint(manager, monkeypatch):
    example = example_with_backup()
    with manager.session(at=NOW) as store:
        store.set_policy(example.policy)
        before = count(store, "retrievals")
        from collections import namedtuple

        usage = namedtuple("usage", "total used free")
        monkeypatch.setattr(
            "ghana_cti_pipeline.storage.capacity.shutil.disk_usage", lambda _: usage(1, 1, 0)
        )
        with pytest.raises(StoreError, match="capacity_pause"):
            example.commit(store)
        assert count(store, "retrievals") == before
        assert store.get_checkpoint(example.context, at=NOW) is None


def test_process_lock_contention_is_bounded(manager, authority):
    with manager.session(at=NOW):
        with pytest.raises(StoreError, match="workspace_busy"):
            LifecycleStore(manager.root, authority, at=NOW)
    with manager.session(at=NOW):
        pass


def test_readonly_sqlite_error_rolls_back_without_advancing(manager):
    example = example_with_backup()
    install(manager, example)
    with manager.session(at=NOW) as store:
        checkpoint = store.get_checkpoint(example.context, at=NOW)
        store._db.execute("PRAGMA query_only=ON")
        with pytest.raises(StoreError, match="storage_error"):
            case(cycle=1).commit(store)
        store._db.execute("PRAGMA query_only=OFF")
        assert store.get_checkpoint(example.context, at=NOW) == checkpoint
        assert count(store, "retrievals") == 1


def test_sqlite_full_autorollback_keeps_prior_checkpoint(manager, monkeypatch):
    example = example_with_backup()
    install(manager, example)
    with manager.session(at=NOW) as store:
        before = store.get_checkpoint(example.context, at=NOW)
        pages = store._db.execute("PRAGMA page_count").fetchone()[0]
        store._db.execute(f"PRAGMA max_page_count={pages}")
        monkeypatch.setattr(store.workspace, "constrain", lambda *args: None)
        huge = case(cycle=1, original="<p>" + "synthetic " * 80000 + "</p>")
        with pytest.raises(StoreError, match="storage_error"):
            huge.commit(store)
        assert store.get_checkpoint(example.context, at=NOW) == before
        assert count(store, "retrievals") == 1


def test_crash_after_writes_recovers_hot_journal(tmp_path, manager):
    example = example_with_backup()
    install(manager, example)
    script = """
import os, sys
from datetime import timedelta
from pathlib import Path
from storage_cases import NOW, case
from ghana_cti_pipeline.storage.lifecycle import LifecycleStore
from ghana_cti_pipeline.storage.rights_ledger import LedgerAuthority
root=Path(sys.argv[1])
authority=LedgerAuthority(basis="https://example.org/synthetic-ledger-basis",retain_until=NOW+timedelta(days=2000))
manager=LifecycleStore(root,authority,at=NOW)
with manager.session(at=NOW) as store:
    def crash(checkpoint):
        os._exit(91)
    store._save_checkpoint=crash
    store._db.execute("PRAGMA cache_size=5")
    case(cycle=1,original="<p>" + "synthetic crash " * 20000 + "</p>").commit(store)
"""
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent))
    result = subprocess.run(
        [sys.executable, "-c", script, str(manager.root)],
        env=environment,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 91, "synthetic child did not reach crash point"
    assert (manager.root / "live.sqlite-journal").exists()
    with manager.session(at=NOW) as store:
        assert verify_store(store, at=NOW)["retrievals"] == 1
        assert (
            store.get_checkpoint(example.context, at=NOW).last_retrieval_id
            == example.manifest.retrieval.retrieval_id
        )
    assert not (manager.root / "live.sqlite-journal").exists()


def test_backup_deadline_retires_copies_without_shortening_live_policy(manager):
    example = example_with_backup()
    deadline = NOW + timedelta(minutes=1)
    example = replace(
        example,
        policy=example.policy.model_copy(
            update={"retention": example.policy.retention.model_copy(update={"backups": deadline})}
        ),
    )
    install(manager, example)
    backup = manager.backup(at=NOW)
    with pytest.raises(StoreError, match="backup_expired"):
        manager.restore(backup, at=deadline)
    with pytest.raises(StoreError, match="maintenance_required"), manager.session(at=deadline):
        pass
    assert manager.purge(at=deadline)["policies_removed"] == 0
    with manager.session(at=deadline) as store:
        assert store.get_checkpoint(example.context, at=deadline)
    with pytest.raises(StoreError, match="backup_policy_denied"):
        manager.backup(at=deadline)


@pytest.mark.parametrize("mutation", ["schema", "blob", "manifest", "derivation", "fk"])
def test_restore_verifies_graph_even_with_matching_outer_digest(manager, monkeypatch, mutation):
    install(manager, example_with_backup())
    backup = manager.backup(at=NOW)
    path = manager.root / "backups" / f"{backup}.sqlite"
    from ghana_cti_pipeline.storage.lifecycle import file_digest

    original_digest = file_digest(path)
    with closing(sqlite3.connect(path, isolation_level=None)) as db:
        if mutation == "schema":
            db.execute("PRAGMA user_version=999")
        elif mutation == "blob":
            db.execute("UPDATE blobs SET body=?", (b"synthetic corruption",))
        elif mutation == "manifest":
            db.execute("UPDATE manifests SET payload='{}'")
        elif mutation == "derivation":
            db.execute("UPDATE derivations SET payload='{}'")
        else:
            db.execute("DELETE FROM artifacts")
    # Independently exercise structural verification rather than only file-checksum rejection.
    monkeypatch.setattr(
        "ghana_cti_pipeline.storage.lifecycle.file_digest", lambda _: original_digest
    )
    with pytest.raises(StoreError):
        manager.restore(backup, at=NOW)
    assert not list((manager.root / "restores").iterdir())


def test_wal_recovery_and_purge_remove_managed_canary(manager):
    example = example_with_backup(original="<p>SYNTHETIC_WAL_CANARY_04</p>")
    install(manager, example)
    script = """
import os, sqlite3, sys
connection=sqlite3.connect(sys.argv[1],isolation_level=None)
connection.execute("PRAGMA journal_mode=WAL")
connection.execute("PRAGMA wal_autocheckpoint=0")
connection.execute("BEGIN IMMEDIATE")
connection.execute("UPDATE blobs SET body=CAST(body || x'21' AS BLOB)")
connection.execute("UPDATE blobs SET body=substr(body,1,length(body)-1)")
connection.execute("COMMIT")
os._exit(92)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(manager.root / "live.sqlite")],
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 92
    wal = manager.root / "live.sqlite-wal"
    assert b"SYNTHETIC_WAL_CANARY_04" in wal.read_bytes()
    manager.purge(at=NOW, revoke=(example.policy.reference,))
    assert not wal.exists()
    assert not (manager.root / "live.sqlite-shm").exists()
    for path in manager.workspace.inventory():
        assert b"SYNTHETIC_WAL_CANARY_04" not in path.read_bytes()


def test_interrupted_backup_is_not_a_restore_source_and_requires_cleanup(manager, monkeypatch):
    install(manager, example_with_backup())
    original = manager._event

    def fail_registration(ledger, action, key, detail, at):
        if action == "backup":
            raise OSError("synthetic interruption after snapshot publication")
        return original(ledger, action, key, detail, at)

    with monkeypatch.context() as patch:
        patch.setattr(manager, "_event", fail_registration)
        with pytest.raises(StoreError):
            manager.backup(at=NOW)
    orphan = next((manager.root / "backups").iterdir())
    with pytest.raises(StoreError, match="unavailable_backup"):
        manager.restore(orphan.stem, at=NOW)
    with pytest.raises(StoreError, match="maintenance_required"), manager.session(at=NOW):
        pass
    manager.purge(at=NOW)
    with manager.session(at=NOW) as store:
        assert verify_store(store, at=NOW)["manifests"] == 1


def test_ledger_corruption_and_expired_authority_block_use(manager, authority):
    example = example_with_backup()
    install(manager, example)
    manager.backup(at=NOW)
    with pytest.raises(StoreError, match="ledger_authority_expired"):
        manager.diagnostics(at=authority.retain_until)
    with closing(sqlite3.connect(manager.root / "rights.sqlite", isolation_level=None)) as db:
        db.execute("DROP TRIGGER no_events_UPDATE")
        db.execute("UPDATE events SET digest='corrupt'")
    with pytest.raises(StoreError), manager.session(at=NOW):
        pass
    with pytest.raises(StoreError):
        manager.purge(at=NOW)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "mode", "unknown"])
def test_unsafe_workspace_entries_are_rejected(manager, tmp_path, kind):
    path = manager.root / "staging" / f"{uuid4()}.sqlite"
    outside = tmp_path / "synthetic-outside"
    outside.write_bytes(b"synthetic")
    outside.chmod(0o600)
    if kind == "symlink":
        path.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, path)
    elif kind == "mode":
        path.write_bytes(b"synthetic")
        path.chmod(0o644)
    else:
        (manager.root / "unknown").write_bytes(b"synthetic")
    with pytest.raises(StoreError):
        manager.purge(at=NOW)
    assert outside.read_bytes() == b"synthetic"


def test_process_crash_during_purge_keeps_durable_block_until_retry(manager):
    example = example_with_backup(original="<p>SYNTHETIC_PURGE_CRASH_04</p>")
    install(manager, example)
    manager.backup(at=NOW)
    script = """
import os, sys
from datetime import timedelta
from pathlib import Path
from storage_cases import NOW, case
from ghana_cti_pipeline.storage.lifecycle import LifecycleStore
from ghana_cti_pipeline.storage.rights_ledger import LedgerAuthority
authority=LedgerAuthority(basis="https://example.org/synthetic-ledger-basis",retain_until=NOW+timedelta(days=2000))
manager=LifecycleStore(Path(sys.argv[1]),authority,at=NOW)
manager._compact=lambda path: os._exit(93)
manager.purge(at=NOW,revoke=(case().policy.reference,))
"""
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent))
    result = subprocess.run(
        [sys.executable, "-c", script, str(manager.root)],
        env=environment,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 93
    assert manager.diagnostics(at=NOW)["pending"] == 1
    with pytest.raises(StoreError, match="maintenance_required"), manager.session(at=NOW):
        pass
    manager.purge(at=NOW)
    assert manager.diagnostics(at=NOW)["pending"] == 0
    for path in manager.workspace.inventory():
        assert b"SYNTHETIC_PURGE_CRASH_04" not in path.read_bytes()


def test_isolated_restore_works_when_live_database_is_missing(manager, authority):
    install(manager, example_with_backup())
    backup = manager.backup(at=NOW)
    (manager.root / "live.sqlite").unlink()
    reopened = LifecycleStore(manager.root, authority, at=NOW)
    with pytest.raises(StoreError, match="missing_live_database"), reopened.session(at=NOW):
        pass
    candidate = reopened.restore(backup, at=NOW)
    with SQLiteEvidenceStore(candidate) as store:
        assert verify_store(store, at=NOW)["manifests"] == 1
        assert count(store, "checkpoints") == 0
    assert not (manager.root / "live.sqlite").exists()


def test_lifecycle_preserves_revision_derivation_and_304_history(manager):
    from storage_cases import not_modified

    example = example_with_backup()
    install(manager, example)
    again = case(cycle=2)
    at = NOW + timedelta(minutes=4)
    with manager.session(at=NOW) as store:
        case(cycle=1, original="<p>synthetic B</p>").commit(store)
        again.commit(store)
        store.record_not_modified(not_modified(again), again.context, at=at)
        case(cycle=2, sanitizer="new-version").commit(store, observations=(), at=at)
        assert count(store, "revisions") == 2
        assert count(store, "observations") == 3
        assert count(store, "retrievals") == 4
    backup = manager.backup(at=at)
    candidate = manager.restore(backup, at=at)
    with SQLiteEvidenceStore(candidate) as store:
        report = verify_store(store, at=at)
        assert report["manifests"] == 4
        assert report["retrievals"] == 4
        assert count(store, "checks") == 1
        assert count(store, "checkpoints") == 0
    manager.purge(at=at, revoke=(example.policy.reference,))
    with manager.session(at=at) as store:
        assert verify_store(store, at=at)["retrievals"] == 0
