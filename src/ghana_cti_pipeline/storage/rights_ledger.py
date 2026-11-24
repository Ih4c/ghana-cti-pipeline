"""Independent append-only opaque rights ledger; never part of evidence restore."""

import hashlib
import sqlite3
from pathlib import Path
from typing import Literal

from ghana_cti_pipeline.core.digests import canonical_json
from ghana_cti_pipeline.core.evidence_values import EvidenceContract, ReferenceURL, Timestamp
from ghana_cti_pipeline.storage.capacity import checked, private_file
from ghana_cti_pipeline.storage.records import StoreError, serialized
from ghana_cti_pipeline.storage.validation import time_key

ACTIONS = {"revoke", "expire", "select", "pending", "complete", "backup", "retire"}
ZERO = "0" * 64


class LedgerAuthority(EvidenceContract):
    kind: Literal["ledger_authority"] = "ledger_authority"
    basis: ReferenceURL
    retain_until: Timestamp


def fingerprint(value) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def policy_key(reference) -> str:
    return fingerprint(reference.model_dump(mode="json"))


class RightsLedger:
    def __init__(self, path: Path, authority: LedgerAuthority, *, create=False):
        authority = LedgerAuthority.model_validate(authority)
        if create:
            private_file(path)
        checked(path)
        self.db = sqlite3.connect(path, isolation_level=None, timeout=0.1)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.execute("PRAGMA trusted_schema=OFF")
            self.db.execute("PRAGMA synchronous=FULL")
            if create:
                self.db.execute("BEGIN IMMEDIATE")
                self.db.execute("PRAGMA application_id=1195594828")
                self.db.execute("PRAGMA user_version=1")
                self.db.execute("CREATE TABLE authority (payload TEXT NOT NULL)")
                self.db.execute("INSERT INTO authority VALUES (?)", (serialized(authority),))
                self.db.execute(
                    "CREATE TABLE events (sequence INTEGER PRIMARY KEY, "
                    "event_id TEXT UNIQUE NOT NULL, "
                    "payload TEXT NOT NULL, previous TEXT NOT NULL, digest TEXT NOT NULL)"
                )
                for table in ("authority", "events"):
                    for action in ("UPDATE", "DELETE"):
                        self.db.execute(
                            f"CREATE TRIGGER no_{table}_{action} BEFORE {action} ON {table} "
                            "BEGIN SELECT RAISE(ABORT, 'append_only'); END"
                        )
                self.db.execute("COMMIT")
            if (
                self.db.execute("PRAGMA application_id").fetchone()[0] != 1195594828
                or self.db.execute("PRAGMA user_version").fetchone()[0] != 1
                or [r[0] for r in self.db.execute("SELECT payload FROM authority")]
                != [serialized(authority)]
            ):
                raise StoreError("ledger_mismatch")
            expected_triggers = {
                f"no_{table}_{action}"
                for table in ("authority", "events")
                for action in ("UPDATE", "DELETE")
            }
            if {
                r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            } != expected_triggers:
                raise StoreError("ledger_mismatch")
            self.events()
            if self.db.execute("PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
                raise StoreError("ledger_journal_mode")
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def events(self):
        import json

        previous = ZERO
        result = []
        for sequence, row in enumerate(
            self.db.execute("SELECT * FROM events ORDER BY sequence"), 1
        ):
            payload = json.loads(row["payload"])
            if (
                row["sequence"] != sequence
                or row["previous"] != previous
                or payload["action"] not in ACTIONS
                or row["event_id"] != fingerprint([payload["action"], payload["key"]])
                or row["digest"] != fingerprint([sequence, previous, payload])
                or canonical_json(payload).decode() != row["payload"]
            ):
                raise StoreError("corrupt_ledger")
            previous = row["digest"]
            result.append(dict(row) | {"value": payload})
        return result

    def append(self, action, key, detail, at):
        if action not in ACTIONS:
            raise StoreError("invalid_ledger_action")
        event_id = fingerprint([action, key])
        rows = self.events()
        for row in rows:
            if row["event_id"] == event_id:
                if row["value"]["detail"] != detail:
                    raise StoreError("ledger_conflict")
                return row
        sequence = len(rows) + 1
        previous = rows[-1]["digest"] if rows else ZERO
        payload = {"action": action, "key": key, "detail": detail, "at": time_key(at)}
        self.db.execute(
            "INSERT INTO events VALUES (?,?,?,?,?)",
            (
                sequence,
                event_id,
                canonical_json(payload).decode(),
                previous,
                fingerprint([sequence, previous, payload]),
            ),
        )
        return self.events()[-1]

    def blocked(self):
        return {
            r["value"]["key"] for r in self.events() if r["value"]["action"] in {"revoke", "expire"}
        }

    def pending(self):
        values = [r["value"] for r in self.events()]
        completed = {v["key"] for v in values if v["action"] == "complete"}
        return [v["key"] for v in values if v["action"] == "pending" and v["key"] not in completed]
