"""Temporary SQLite databases and synthetic byte fixtures only; no live sources."""

import sqlite3
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import pytest
from storage_cases import NOW, case, not_modified

from ghana_cti_pipeline.core.artifacts import ArtifactAvailability
from ghana_cti_pipeline.core.identities import (
    evidence_association_id,
    processing_manifest_digest,
    processing_manifest_id,
)
from ghana_cti_pipeline.core.retrieval import RetrievalFailure
from ghana_cti_pipeline.storage.records import StoreError
from ghana_cti_pipeline.storage.sqlite import SQLiteEvidenceStore
from ghana_cti_pipeline.storage.sqlite_schema import TABLES


@pytest.fixture
def store(tmp_path):
    with SQLiteEvidenceStore(tmp_path / "synthetic.sqlite") as value:
        yield value


def counts(store):
    return {
        name: store._db.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in TABLES
    }


def install(store, example):
    store.set_policy(example.policy)
    example.commit(store)


def rebound(manifest):
    manifest = manifest.model_copy(update={"digest": processing_manifest_digest(manifest)})
    return manifest.model_copy(update={"manifest_id": processing_manifest_id(manifest)})


@pytest.mark.parametrize("base", ["microsoft", "google", "catalog"])
def test_atomic_round_trip_reopen_and_replay(tmp_path, base):
    example = case(base)
    path = tmp_path / "synthetic.sqlite"
    with SQLiteEvidenceStore(path) as store:
        install(store, example)
        before = counts(store)
        checkpoint = store.get_checkpoint(example.context, at=NOW)
        assert checkpoint.manifest_id == example.manifest.manifest_id
        for artifact_id, body in example.bodies.items():
            assert store.get_artifact(artifact_id, at=NOW) == body
        bundle = example.evidence[0]
        assert store.get_evidence(evidence_association_id(bundle)) == bundle
        assert (
            store.get_retrieval(example.manifest.retrieval.retrieval_id)
            == example.manifest.retrieval
        )
        assert store._db.execute("PRAGMA foreign_key_check").fetchall() == []
    assert path.stat().st_mode & 0o077 == 0
    with SQLiteEvidenceStore(path) as store:
        example.commit(store, at=NOW + timedelta(minutes=1))
        assert counts(store) == before
        assert store.get_checkpoint(example.context, at=NOW + timedelta(minutes=1)) == checkpoint


def test_a_b_a_and_reprocessing_keep_immutable_history(store):
    a, b, again = case(), case(cycle=1, original="<p>synthetic B</p>"), case(cycle=2)
    install(store, a)
    b.commit(store)
    again.commit(store)
    assert counts(store)["revisions"] == 2
    assert counts(store)["evidence"] == counts(store)["observations"] == 3
    assert a.evidence[0].evidence_id == again.evidence[0].evidence_id
    assert evidence_association_id(a.evidence[0]) != evidence_association_id(again.evidence[0])
    current = store.get_checkpoint(again.context, at=NOW)
    a.commit(store)  # Old exact replay cannot rewind the newest check.
    assert store.get_checkpoint(again.context, at=NOW) == current
    transformed = case(cycle=2, sanitizer="s2")
    transformed.commit(store, observations=())
    assert counts(store)["revisions"] == 2
    assert counts(store)["evidence"] == 4
    assert counts(store)["retrievals"] == counts(store)["observations"] == 3
    assert counts(store)["derivations"] == 6  # A/B chains plus the revised A chain.
    assert store.get_checkpoint(again.context, at=NOW) is None
    assert store.get_checkpoint(transformed.context, at=NOW) is not None
    assert store.get_evidence(evidence_association_id(a.evidence[0])) == a.evidence[0]


def test_conflicting_immutable_policy_and_retrieval_rollback(store):
    example = case()
    install(store, example)
    before = counts(store)
    with pytest.raises(StoreError, match="immutable_conflict"):
        store.set_policy(example.policy.model_copy(update={"purpose": "conflicting purpose"}))
    different = case(original="<p>different bytes with same retrieval ID</p>")
    with pytest.raises(StoreError, match="immutable_conflict"):
        different.commit(store)
    assert counts(store) == before
    assert store.get_checkpoint(example.context, at=NOW) is not None


def test_partial_write_exception_rolls_back_whole_batch(store, monkeypatch):
    example = case()
    store.set_policy(example.policy)
    before = counts(store)

    def fail(checkpoint):
        assert counts(store)["manifests"] == 1
        raise RuntimeError("synthetic interruption after writes")

    with monkeypatch.context() as guard:
        guard.setattr(store, "_save_checkpoint", fail)
        with pytest.raises(RuntimeError, match="synthetic interruption"):
            example.commit(store)
    assert counts(store) == before
    assert store.get_checkpoint(example.context, at=NOW) is None
    example.commit(store)
    assert store.get_checkpoint(example.context, at=NOW) is not None


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_body",
        "extra_body",
        "wrong_length",
        "wrong_hash",
        "missing_observation",
        "incomplete",
    ],
)
def test_invalid_batch_never_writes_or_advances(store, mutation):
    example = case()
    store.set_policy(example.policy)
    before = counts(store)
    bodies = dict(example.bodies)
    key = example.manifest.response.artifact_id
    observations = example.observations
    manifest = example.manifest
    if mutation == "missing_body":
        del bodies[key]
    elif mutation == "extra_body":
        bodies[UUID(int=99999)] = b"synthetic"
    elif mutation == "wrong_length":
        bodies[key] += b"x"
    elif mutation == "wrong_hash":
        bodies[key] = b"!" * len(bodies[key])
    elif mutation == "missing_observation":
        observations = ()
    else:
        manifest = rebound(manifest.model_copy(update={"completeness": "incomplete"}))
    with pytest.raises(StoreError):
        store.commit_batch(manifest, example.evidence, bodies, observations, at=NOW)
    assert counts(store) == before


@pytest.mark.parametrize(
    "mutation", ["unresolved", "expired", "future", "retention", "scope", "endpoint", "review"]
)
def test_policy_gates_do_not_claim_rights(store, mutation):
    example = case()
    changes = {
        "unresolved": {"basis_status": "unresolved"},
        "expired": {"expires_at": NOW},
        "future": {"effective_at": NOW + timedelta(days=1)},
        "retention": {"retention": example.policy.retention.model_copy(update={"original": NOW})},
        "scope": {"permitted_processing": ("retrieve", "retain")},
        "endpoint": {"endpoint": "https://example.org/different"},
        "review": {"reviewed_at": NOW + timedelta(days=1)},
    }
    store.set_policy(example.policy.model_copy(update=changes[mutation]))
    before = counts(store)
    with pytest.raises(StoreError, match="policy_denied"):
        example.commit(store)
    assert counts(store) == before


def test_valid_304_chain_is_idempotent_and_adds_no_item_evidence(store):
    example = case()
    install(store, example)
    before = counts(store)
    first = not_modified(example)
    store.record_not_modified(first, example.context, at=NOW + timedelta(minutes=2))
    second = not_modified(example, number=1, sent_etag='"synthetic-v2"', returned_etag=None)
    store.record_not_modified(second, example.context, at=NOW + timedelta(minutes=4))
    checkpoint = store.get_checkpoint(example.context, at=NOW + timedelta(minutes=4))
    assert checkpoint.last_retrieval_id == second.retrieval_id
    assert checkpoint.representation_retrieval_id == example.manifest.retrieval.retrieval_id
    assert checkpoint.etag == '"synthetic-v2"'
    assert checkpoint.last_modified == example.manifest.retrieval.returned_last_modified
    after = counts(store)
    for table in TABLES - {"retrievals", "checks"}:
        assert after[table] == before[table]
    assert after["retrievals"] == before["retrievals"] + 2
    store.record_not_modified(first, example.context, at=NOW + timedelta(minutes=5))
    assert counts(store) == after
    assert store.get_checkpoint(example.context, at=NOW + timedelta(minutes=5)) == checkpoint
    transformed = case(sanitizer="different")
    transformed.commit(store, observations=(), at=NOW + timedelta(minutes=5))
    updated = store.get_checkpoint(transformed.context, at=NOW + timedelta(minutes=5))
    assert updated.last_checked_at == second.ended_at
    assert updated.etag == checkpoint.etag


@pytest.mark.parametrize(
    "mutation",
    ["source", "requested", "redirect", "anchor", "etag", "modified", "time", "no_store", "vary"],
)
def test_invalid_304_never_advances_checkpoint(store, mutation):
    example = case()
    install(store, example)
    receipt = not_modified(example)
    changes = {
        "source": {"source_id": "wrong-source"},
        "requested": {
            "requested_url": "https://example.org/other",
            "final_url": "https://example.org/other",
        },
        "redirect": {
            "final_url": "https://example.org/redirect",
            "redirect_urls": ("https://example.org/redirect",),
        },
        "anchor": {"representation_retrieval_id": UUID(int=9876)},
        "etag": {"sent_etag": '"wrong"'},
        "modified": {"sent_last_modified": "wrong"},
        "time": {"started_at": NOW - timedelta(hours=2)},
        "no_store": {"cache_control": "public, NO-STORE"},
        "vary": {"vary": "*"},
    }
    before = counts(store)
    checkpoint = store.get_checkpoint(example.context, at=NOW)
    with pytest.raises(StoreError, match="invalid_304"):
        store.record_not_modified(
            receipt.model_copy(update=changes[mutation]),
            example.context,
            at=NOW + timedelta(minutes=2),
        )
    assert counts(store) == before
    assert store.get_checkpoint(example.context, at=NOW) == checkpoint


@pytest.mark.parametrize(
    "table",
    [
        "blobs",
        "artifacts",
        "availability",
        "evidence",
        "revisions",
        "derivations",
        "observations",
        "manifest_evidence",
        "manifest_artifacts",
        "evidence_artifacts",
        "evidence_derivations",
        "retrievals",
        "policies",
    ],
)
def test_missing_backing_invalidates_conditional_state_without_repair(store, table):
    example = case()
    install(store, example)
    # Simulate offline damage; normal API writes have foreign keys enabled.
    store._db.execute("PRAGMA foreign_keys=OFF")
    store._db.execute(f"DELETE FROM {table}")
    store._db.execute("PRAGMA foreign_keys=ON")
    before = counts(store)
    assert store.get_checkpoint(example.context, at=NOW) is None
    with pytest.raises(StoreError):
        store.record_not_modified(
            not_modified(example), example.context, at=NOW + timedelta(minutes=2)
        )
    with pytest.raises(StoreError):
        example.commit(store)
    assert counts(store) == before


@pytest.mark.parametrize(
    "table",
    [
        "blobs",
        "artifacts",
        "evidence",
        "manifests",
        "retrievals",
        "availability",
        "revisions",
        "derivations",
    ],
)
def test_corrupt_bytes_or_descriptors_are_not_304_backing(store, table):
    example = case()
    install(store, example)
    column, value = ("body", b"synthetic corruption") if table == "blobs" else ("payload", "{}")
    store._db.execute(f"UPDATE {table} SET {column}=?", (value,))
    assert store.get_checkpoint(example.context, at=NOW) is None
    with pytest.raises(StoreError):
        store.record_not_modified(
            not_modified(example), example.context, at=NOW + timedelta(minutes=2)
        )


def test_expiry_policy_change_and_unavailable_artifact_disable_checkpoint(store):
    example = case()
    install(store, example)
    assert store.get_checkpoint(example.context, at=example.policy.expires_at) is None
    original = example.evidence[0].original
    event = ArtifactAvailability(
        kind="artifact_availability",
        artifact_id=original.artifact_id,
        policy=original.policy,
        state="unavailable",
        recorded_at=NOW + timedelta(seconds=1),
        retention_until=example.policy.retention.original,
    )
    store.record_availability(event, at=NOW + timedelta(seconds=1))
    assert store.get_checkpoint(example.context, at=NOW + timedelta(seconds=1)) is None
    with pytest.raises(StoreError, match="unavailable_backing"):
        store.get_artifact(original.artifact_id, at=NOW + timedelta(seconds=1))
    with pytest.raises(StoreError):
        example.commit(store, at=NOW + timedelta(seconds=1))
    new = example.policy.model_copy(
        update={"reference": example.policy.reference.model_copy(update={"policy_version": "new"})}
    )
    store.set_policy(new)
    assert store.get_checkpoint(example.context, at=NOW) is None


@pytest.mark.parametrize(
    "field", ["request_variant_id", "adapter_version", "parser_version", "processing_profile"]
)
def test_changed_context_requires_complete_reprocessing(store, field):
    example = case()
    install(store, example)
    context = example.context.model_copy(update={field: "different"})
    assert store.get_checkpoint(context, at=NOW) is None
    with pytest.raises(StoreError):
        store.record_not_modified(not_modified(example), context, at=NOW + timedelta(minutes=2))


def test_failure_receipts_and_other_source_survive_source_failure(store):
    good = case()
    install(store, good)
    before = store.get_checkpoint(good.context, at=NOW)
    other = case("catalog", cycle=10)
    store.set_policy(other.policy)
    bad = dict(other.bodies)
    bad[other.manifest.response.artifact_id] += b"!"
    with pytest.raises(StoreError):
        store.commit_batch(other.manifest, other.evidence, bad, other.observations, at=NOW)
    failure = RetrievalFailure(
        kind="retrieval_failure",
        retrieval_id=UUID(int=9876),
        source_id=good.policy.reference.source_id,
        requested_url=good.policy.endpoint,
        started_at=NOW,
        ended_at=NOW,
        code="timeout",
        retryable=True,
    )
    store.record_failure(failure)
    store.record_failure(failure)
    assert store.get_checkpoint(good.context, at=NOW) == before
    other.commit(store)
    assert store.get_checkpoint(other.context, at=NOW) is not None


def test_foreign_keys_and_sql_failure_roll_back(store):
    assert store._db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError), store._transaction():
        store._db.execute("INSERT INTO manifest_artifacts VALUES (?,?)", ("missing", "missing"))
    example = case()
    store.set_policy(example.policy)
    before = counts(store)
    store._db.execute(
        "CREATE TEMP TRIGGER fail_observation BEFORE INSERT ON observations "
        "BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END"
    )
    with pytest.raises(StoreError, match="^storage_error$"):
        example.commit(store)
    assert counts(store) == before
    store._db.execute("DROP TRIGGER fail_observation")
    example.commit(store)


def test_schema_mismatch_and_unsafe_paths_reject(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    with SQLiteEvidenceStore(path) as store:
        store._db.execute("PRAGMA user_version=999")
    with pytest.raises(StoreError, match="unsupported_database_schema"):
        SQLiteEvidenceStore(path)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 999
    link = tmp_path / "link.sqlite"
    link.symlink_to(path)
    with pytest.raises(StoreError, match="unsafe_database_path"):
        SQLiteEvidenceStore(link)
    path.chmod(0o644)
    with pytest.raises(StoreError, match="unsafe_database_path"):
        SQLiteEvidenceStore(path)


def test_cache_controls_and_empty_complete_feed(store):
    denied = case(cache_control="private, no-store")
    store.set_policy(denied.policy)
    with pytest.raises(StoreError, match="cache_policy_denied"):
        denied.commit(store)
    unknown = case(vary="Cookie")
    unknown.commit(store)
    assert store.get_checkpoint(unknown.context, at=NOW) is None
    empty = case(cycle=1)
    manifest = rebound(
        empty.manifest.model_copy(update={"items": (), "artifacts": (), "expected_item_count": 0})
    )
    empty = replace(
        empty,
        manifest=manifest,
        evidence=(),
        observations=(),
        bodies={manifest.response.artifact_id: empty.bodies[manifest.response.artifact_id]},
    )
    empty.commit(store)
    assert store.get_checkpoint(empty.context, at=NOW) is not None
    store.record_not_modified(not_modified(empty), empty.context, at=NOW + timedelta(minutes=2))
    assert counts(store)["observations"] == 1  # Only the earlier nonempty batch.


@pytest.fixture(autouse=True)
def block_dns(monkeypatch):
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("DNS is forbidden in offline storage tests")

    monkeypatch.setattr(socket, "getaddrinfo", denied)


@pytest.mark.parametrize(
    "group", ["response", "original", "derived", "metadata", "digests", "audit"]
)
def test_each_retention_deadline_is_exclusive(store, group):
    example = case()
    deadline = NOW + timedelta(seconds=1)
    policy = example.policy.model_copy(
        update={"retention": example.policy.retention.model_copy(update={group: deadline})}
    )
    store.set_policy(policy)
    example.commit(store)
    assert store.get_checkpoint(example.context, at=NOW) is not None
    assert store.get_checkpoint(example.context, at=deadline) is None
    before = counts(store)
    with pytest.raises(StoreError):
        store.record_not_modified(
            not_modified(example), example.context, at=NOW + timedelta(minutes=2)
        )
    assert counts(store) == before


@pytest.mark.parametrize(
    "table", ["evidence_artifacts", "evidence_derivations", "manifest_artifacts"]
)
def test_unexpected_association_edges_are_corrupt_backing(store, table):
    example = case()
    install(store, example)
    if table == "manifest_artifacts":
        other = case(cycle=1, original="<p>different synthetic item</p>")
        other.commit(store)
        store._db.execute(
            "INSERT INTO manifest_artifacts VALUES (?,?)",
            (str(other.manifest.manifest_id), str(example.manifest.response.artifact_id)),
        )
        example = other
    else:
        row = store._db.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        store._db.execute(f"INSERT INTO {table} VALUES (?,?,?)", (row[0], "unexpected", row[2]))
    assert store.get_checkpoint(example.context, at=NOW) is None


@pytest.mark.parametrize(
    "damage", ["missing_check", "cycle", "validator", "304_anchor", "manifest"]
)
def test_304_chain_must_be_intact(store, damage):
    example = case()
    install(store, example)
    receipt = not_modified(example)
    at = NOW + timedelta(minutes=2)
    store.record_not_modified(receipt, example.context, at=at)
    checkpoint = store.get_checkpoint(example.context, at=at)
    if damage == "missing_check":
        store._db.execute("DELETE FROM checks")
    elif damage == "cycle":
        store._db.execute("UPDATE checks SET previous_id=retrieval_id")
    elif damage == "validator":
        store._save_checkpoint(checkpoint.model_copy(update={"etag": '"invented"'}))
    elif damage == "manifest":
        store._db.execute("PRAGMA foreign_keys=OFF")
        store._db.execute("DELETE FROM manifests")
        store._db.execute("PRAGMA foreign_keys=ON")
    else:
        later = not_modified(example, number=1, sent_etag='"synthetic-v2"')
        later = later.model_copy(update={"representation_retrieval_id": receipt.retrieval_id})
        before = counts(store)
        with pytest.raises(StoreError, match="invalid_304"):
            store.record_not_modified(later, example.context, at=NOW + timedelta(minutes=4))
        assert counts(store) == before
        return
    assert store.get_checkpoint(example.context, at=at) is None
    with pytest.raises(StoreError):
        store.record_not_modified(
            not_modified(example, number=1, sent_etag='"synthetic-v2"'),
            example.context,
            at=NOW + timedelta(minutes=4),
        )


def test_304_write_failure_rolls_back_receipt_and_checkpoint(store, monkeypatch):
    example = case()
    install(store, example)
    before = counts(store)
    checkpoint = store.get_checkpoint(example.context, at=NOW)

    def fail(value):
        assert counts(store)["checks"] == 1
        raise RuntimeError("synthetic 304 interruption")

    with monkeypatch.context() as guard:
        guard.setattr(store, "_save_checkpoint", fail)
        with pytest.raises(RuntimeError):
            store.record_not_modified(
                not_modified(example), example.context, at=NOW + timedelta(minutes=2)
            )
    assert counts(store) == before
    assert store.get_checkpoint(example.context, at=NOW) == checkpoint


def test_two_connections_replay_and_locked_writer_do_not_leave_partial_rows(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    example = case()
    with SQLiteEvidenceStore(path) as first, SQLiteEvidenceStore(path) as second:
        install(first, example)
        before = counts(first)
        example.commit(second)
        assert counts(second) == before
        with first._transaction():
            with pytest.raises(StoreError, match="storage_error"):
                case(cycle=1).commit(second)
        assert counts(second) == before
        case(cycle=1).commit(second)
        assert first.get_checkpoint(example.context, at=NOW).last_retrieval_id == UUID(int=1001)


def test_availability_events_are_immutable_and_time_ordered(store):
    example = case()
    install(store, example)
    original = example.evidence[0].original
    event = ArtifactAvailability(
        kind="artifact_availability",
        artifact_id=original.artifact_id,
        policy=original.policy,
        state="deleted",
        recorded_at=NOW + timedelta(seconds=1),
        retention_until=example.policy.retention.original,
    )
    store.record_availability(event, at=event.recorded_at)
    store.record_availability(event, at=event.recorded_at)
    with pytest.raises(StoreError, match="immutable_conflict"):
        store.record_availability(
            event.model_copy(update={"state": "available"}), at=event.recorded_at
        )
    assert store.get_checkpoint(example.context, at=NOW) is not None
    assert store.get_checkpoint(example.context, at=event.recorded_at) is None


@pytest.mark.parametrize("damage", ["bytes", "check_history", "expired"])
def test_exact_304_replay_still_requires_valid_backing(store, damage):
    example = case()
    install(store, example)
    receipt = not_modified(example)
    at = NOW + timedelta(minutes=2)
    store.record_not_modified(receipt, example.context, at=at)
    if damage == "bytes":
        store._db.execute("UPDATE blobs SET body=?", (b"synthetic corruption",))
    elif damage == "check_history":
        store._db.execute("UPDATE checks SET previous_id=retrieval_id")
    else:
        at = example.policy.expires_at
    before = counts(store)
    with pytest.raises(StoreError):
        store.record_not_modified(receipt, example.context, at=at)
    assert counts(store) == before
    assert store.get_checkpoint(example.context, at=at) is None
