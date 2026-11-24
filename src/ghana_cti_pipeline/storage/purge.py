"""Policy-level graph deletion; caller owns ledger, transaction and compaction."""

from ghana_cti_pipeline.storage.rights_ledger import policy_key
from ghana_cti_pipeline.storage.verification import policies


def expired(policy, at):
    return at >= min(
        policy.expires_at,
        *(
            getattr(policy.retention, field)
            for field in ("response", "original", "derived", "metadata", "digests", "audit")
        ),
    )


def delete_policies(store, blocked):
    db = store._db
    selected = {key: p for key, p in policies(store).items() if policy_key(p.reference) in blocked}
    for key, policy in selected.items():
        anchors = {
            r[0] for r in db.execute("SELECT retrieval_id FROM manifests WHERE policy_id=?", (key,))
        }
        checks = {
            r[0]
            for r in db.execute(
                "SELECT retrieval_id FROM checks WHERE manifest_id IN "
                "(SELECT id FROM manifests WHERE policy_id=?)",
                (key,),
            )
        }
        db.execute(
            "DELETE FROM checkpoints WHERE manifest_id IN "
            "(SELECT id FROM manifests WHERE policy_id=?)",
            (key,),
        )
        db.execute(
            "DELETE FROM checks WHERE manifest_id IN (SELECT id FROM manifests WHERE policy_id=?)",
            (key,),
        )
        for table in ("manifest_artifacts", "manifest_evidence"):
            db.execute(
                f"DELETE FROM {table} WHERE manifest_id IN "
                "(SELECT id FROM manifests WHERE policy_id=?)",
                (key,),
            )
        db.execute("DELETE FROM manifests WHERE policy_id=?", (key,))
        db.execute("DELETE FROM observations WHERE policy_id=?", (key,))
        for table in ("evidence_artifacts", "evidence_derivations"):
            db.execute(
                f"DELETE FROM {table} WHERE evidence_id IN "
                "(SELECT id FROM evidence WHERE policy_id=?)",
                (key,),
            )
        db.execute("DELETE FROM evidence WHERE policy_id=?", (key,))
        db.execute(
            "DELETE FROM availability WHERE artifact_id IN "
            "(SELECT id FROM artifacts WHERE policy_id=?)",
            (key,),
        )
        db.execute("DELETE FROM artifacts WHERE policy_id=?", (key,))
        for receipt in checks:
            db.execute("DELETE FROM retrievals WHERE id=?", (receipt,))
        for receipt in anchors:
            db.execute("DELETE FROM retrievals WHERE id=?", (receipt,))
        # Failure receipts have source-level, not policy-level, attribution; retire conservatively.
        db.execute(
            "DELETE FROM retrievals WHERE source_id=? AND kind='retrieval_failure'",
            (policy.reference.source_id,),
        )
        db.execute("DELETE FROM current_policies WHERE policy_id=?", (key,))
        db.execute("DELETE FROM policies WHERE id=?", (key,))
    db.execute(
        "DELETE FROM derivations WHERE id NOT IN (SELECT derivation_id FROM evidence_derivations)"
    )
    db.execute("DELETE FROM revisions WHERE id NOT IN (SELECT revision_id FROM evidence)")
    db.execute(
        "DELETE FROM blobs WHERE NOT EXISTS (SELECT 1 FROM artifacts "
        "WHERE artifacts.domain=blobs.domain AND artifacts.digest=blobs.digest)"
    )
    return len(selected)
