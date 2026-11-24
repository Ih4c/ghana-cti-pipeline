# M1-04 offline recovery and lifecycle

Design binding D029, proposed for independent implementation review, 2026-11-24.
The [owner approval on PR #17](https://github.com/Ih4c/ghana-cti-pipeline/pull/17#issuecomment-7119143529)
covers D017/D020 offline mechanisms, D007 capacity accounting and recovery of the
merged M1-03 store. Base: PR #17 merge `c256b3f`. No source or operational gate is
approved. Use synthetic content and temporary directories only.

## Concrete boundary

The POSIX/Linux `LifecycleStore` facade owns an explicitly supplied private workspace, with
one live schema-v1 database, an independent append-only rights ledger, managed
backup/restore/staging directories and a process lock. Existing core contracts,
M1-03 schema and API remain unchanged. The facade exposes a bounded session for
existing store operations; callers must not open managed files through the raw
M1-03 API. The process lock coordinates compliant callers, not hostile local code.
Symlinks, hard-linked files, unexpected paths and permissive modes fail closed.
Host encryption, trusted parents, filesystem snapshots, swap/dumps and key handling
still require real-host review. No default production paths or jobs are supplied.

Ledger authority is a separate, explicit, time-bounded assertion for opaque
policy hashes and deletion/backup audit events. It is not inherited from a source's
expired audit permission. No content, title, URL or excerpt enters event payloads.
SQL triggers forbid ledger UPDATE/DELETE; sequence/hash chaining detects internal
damage, not malicious rollback without an independently trusted current ledger.
Never restore the ledger from an evidence backup. Missing/damaged ledger blocks use.

## Capacity and failures

The hard ceiling remains 2 GiB, with warning at 80%. Count every regular file in
the managed workspace, including live/ledger databases, journal/WAL/SHM, staging,
isolated restores and backups. Including backups in this ceiling is conservative;
no separate storage purchase or enlarged allowance is implied. Tests may lower,
never raise, the ceiling. Reserve journal, ledger and explicit temporary-copy
headroom before mutations; constrain SQLite page growth as a second guard.
SQLite temporary tables/sorts use memory; compaction uses an explicit managed
VACUUM INTO file. Diagnostics expose counts/safe codes only. Free-space checks
are advisory about other processes, so SQLite/disk errors still roll back.

A nonblocking process lock and SQLite locking prevent competing managed writers.
Crash tests terminate a child inside an uncommitted transaction and reopen the
store, proving journal rollback. Schema mismatch, read-only, contention and
SQLite FULL failures must leave no advanced checkpoint. No schema migration or
silent downgrade is introduced. Failed purge keeps a durable pending event and
blocks serving until an explicit retry completes. Interrupted backup/restore staging and unregistered snapshots
require cleanup before normal sessions resume.

## Backup and isolated restore

Use SQLite's backup API, never copy a live database file. A backup is registered
only after verification, fsync and publication in the private backup directory.
Record its file digest and current ledger anchor. An interrupted unregistered
copy is never a restore source. Require explicit backup permission and unexpired
backup/body/metadata/audit deadlines for every policy included.

Restore only a registered, unretired snapshot with matching digest and a valid
anchor in the current ledger. Work in isolation; verify schema, SQLite integrity,
foreign keys, every BLOB hash/length, immutable derivations/associations, complete
manifests and checkpoint chains. Apply current revocations/expiry, remove
operational policy selections and checkpoints, and verify again. Historical 304
chains remain as evidence. Compact the candidate and retain it only in the managed
restore directory. No automatic replacement of the live store,
source activation or scheduler restart. External copies are outside this mechanism
and must be inventoried and retired by the future approved operator.

## Expiry, revocation and purge

Whole-policy bundles are the deletion unit: the earliest response/original/
derived/metadata/digest/audit deadline or policy expiry retires that policy's
originals, derivatives, evidence/manifest/observation associations and checkpoints.
This deliberately does not preserve derivatives as a rights loophole. Shared
content-addressed BLOBs/revisions remain only while an independently permitted
association references them. A revoked/expired policy version cannot be reused;
a new reviewed policy version is required for any later lawful acquisition.
Backup expiry alone retires backups, without shortening otherwise valid live rights.

Persist opaque revocation/expiry and maintenance intent first. Retire all managed
backups and isolated restore copies conservatively, delete affected rows in one
FK-checked transaction, compact the live database into a controlled file, fsync
and replace it while holding the process lock. Complete the ledger event only
after compaction and journal/WAL/staging checks. Retrying an interrupted operation
must be safe; incomplete maintenance blocks sessions/backup/restore. Mere SQL
DELETE is not success. Synthetic canary tests inspect all remaining managed files.
This establishes logical absence from managed files, not verified physical erasure
from SSDs, copy-on-write history, external backups or storage-provider replicas.

## Manual offline runbook

1. Verify the scope, current rights ledger and independently permitted ledger
   authority. Use a new private temporary workspace and synthetic records only.
2. Inspect capacity before a session. At 80%, plan retention/capacity review; a
   refused reservation is a pause, never permission to increase the cap.
3. On lock contention, close the other managed session and retry explicitly. On
   FULL/read-only errors, retain the safe error code and verify the prior committed
   checkpoint after restoring permitted capacity/access. Do not delete journals.
4. After a process crash, allow SQLite to recover its journal on controlled open.
   Retry pending maintenance explicitly; never remove the ledger or restore an old
   ledger to bypass revocation. Unknown schema needs reviewed migration work.
5. Request backup only with applicable policy scope. Test restore in isolation,
   verify its report and apply the current ledger; never promote an unchecked copy.
6. For expiry/revocation, call the offline purge mechanism. Confirm completion,
   compacted state, retired managed backups and no pending work. A failure is not
   a deletion claim. Inventory external copies and host-specific erasure separately.
7. Stop at the implementation PR. Before B2, independently validate private host,
   encryption, keys, crash/power-loss behavior, filesystem snapshots, capacity,
   lawful retention and deletion deadlines. B1/B2/C and operational jobs stay gated.

## API and verification limits

`LifecycleStore(root, LedgerAuthority(...), at=...)` creates only a fresh private
workspace or opens an existing matching one. The authority must independently
permit opaque ledger retention until its explicit deadline; its assertion is not
legal verification. Missing/corrupt/expired ledger authority blocks operations.
Renewal/migration and independently anchored rollback protection require review;
this increment cannot authenticate an operator-supplied ledger or recover a lost one.

`session(at=...)` exposes the existing M1-03 API under a cooperative process lock
and capacity guards. `diagnostics(at=...)` returns byte counts, the 80% warning,
pending-operation count and retired-policy count. `backup(at=...)` returns a
registered snapshot UUID. `restore(uuid, at=...)` returns a verified private
isolated candidate path; it never promotes that file or recreates a missing live
store. A backup past its backup-retention deadline is rejected. A still-permitted
backup may be filtered for earlier-expired live policy material during isolation.
`purge(at=..., revoke=(PolicyReference(...), ...))` records retirement first,
removes affected policy graphs, retires all managed copies and compacts. Its result
explicitly says `physical_erasure_verified=False`.

The unchanged raw M1-03 class remains available for its original offline tests;
production callers must not bypass the lifecycle facade. Evaluation timestamps
are explicit trusted inputs for reproducible offline tests, not an authenticated
clock. Sessions are short, non-nested, single-owner contexts. No background timer,
automatic retry, automatic restore promotion, migration or key service is included.
The conservative whole-policy purge may delete associated material before its
individual deadline; it does not extend any deadline. Capacity reservation can
pause earlier than the hard ceiling to retain recovery space. If ledger writes or
compaction cannot fit, no completed purge is reported; satisfy headroom/access
without silently raising the cap. Backup files are retired by unlink plus fsync;
physical storage erasure remains outside the verified claim.
