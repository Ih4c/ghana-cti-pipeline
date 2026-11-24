# M1-03 offline SQLite evidence storage

Implementation specification, 2026-11-24; M1 v1.3. The
[owner approval on PR #16](https://github.com/Ih4c/ghana-cti-pipeline/pull/16#issuecomment-7108040658)
covers D005/D013/D019 offline persistence, atomic batches, immutable associations,
foreign keys, replay, rollback and complete 304 backing. PR #16 is merged at
`8a3a85d`; existing contracts, D026 identities and D027 limits remain unchanged.
Only synthetic content and temporary databases are used. This is not production
hosting, rights clearance, source activation, backup/purge or scheduler approval.

## Boundary and schema

`storage/` depends on core contracts/helpers only. Its additive API accepts
explicit database paths, already validated manifests/evidence/observations,
artifact bytes and caller-supplied aware evaluation timestamps. No clock, network,
feed parsing, sanitization or content extraction occurs in the store. Existing V1
`EvidenceRepository` signatures remain unchanged; this V2 store is a separate API.

D028 records these concrete implementation bindings for independent review.
SQLite uses application ID `0x47435449` and database schema version 1. Initialize
only an empty database; reject foreign/unsupported schemas without migration.
Enable foreign keys, explicit `BEGIN IMMEDIATE` transactions, rollback-journal
mode and `synchronous=FULL`. WAL tuning, process-crash/storage-pressure recovery,
backup, purge, restore and migration procedures belong to separately approved M1-04.
New files use owner-only permissions; deployment encryption and protected host
directories remain requirements, not capabilities of SQLite or this increment.

Persist immutable policies, retrieval records, domain/SHA-256-addressed BLOBs,
policy-bound artifact associations, source-revision projections, versioned derived
identities, full evidence associations, manifests and observation records. Foreign
keys link all referenced rows, including explicit manifest/evidence/artifact edges.
Current-policy selection and checkpoint pointers are the only mutable operational
selectors; changing a selector never rewrites historical evidence. Availability
assertions are append-only records, not deletion jobs or proof of secure erasure.

Use the D026 evidence association UUID as the full-bundle key; source evidence_id
is a nonunique grouping reference. Derived representation identities exclude
acquisition/policy association details, so stable derived content may have multiple
policy-bound artifact associations. Shared BLOB bytes never share rights or extend
retention. Existing-key/equal-canonical-content is a no-op; different content under
an existing key rejects and rolls back the entire operation. Never use REPLACE.

## Complete 200 batch transaction

Before writing, validate the existing models and M1-02b identity/digest/link
helpers, complete manifest, exact artifact-byte set and required observation links.
Verify each BLOB's declared length and exact SHA-256 and text UTF-8 validity.
Catalog-entry bytes must already use the approved canonical JSON encoding; this
store does not parse source JSON or prove that projected metadata matches it.
The adapter/processing boundary remains responsible for complete source extraction.

Inside one transaction, require the selected policy to match the manifest, source,
endpoint and representation, with documented basis, required processing/artifact
scope, valid effective/expiry dates and unexpired relevant retention deadlines.
These are checks of supplied policy assertions, not independent legal verification.
Store response, source/derived/artifact/evidence associations, manifest, observations,
availability assertions and checkpoint together. A failure leaves no partial batch
or advanced checkpoint. First acquisitions require one observation per manifest
item. Reprocessing a committed 200 may reuse its existing observation links without
creating a new retrieval event; immutable processing manifests stay separate.
Reprocessing requires intact, currently permitted prior manifests for that 200;
it cannot repair missing backing or bypass a policy change. A fresh acquisition
requires later authorized orchestration.

Exact manifest replay is a no-op and cannot rewind a newer checkpoint. It must not
silently restore missing or deleted records. Reusing immutable IDs with conflicting
content fails. Other source transactions remain independently usable after failure.
Failure receipts are stored independently and never advance successful checkpoints.

## Conditional scope and 304

Checkpoint scope includes policy reference, requested endpoint, request variant,
adapter/parser/processing profile and the exact set of transformation descriptors.
The selector key is source/endpoint/request variant. A caller must supply the
currently desired scope; a changed processing scope requires reviewed reprocessing
and a new complete manifest. Merely knowing an old checkpoint key is insufficient.

Eligibility revalidates the committed 200, complete manifest and IDs/digests,
full evidence/artifact edges, source/derived identities, observations, byte counts
and hashes, current policy and latest available/unexpired assertions. Empty valid
feeds still require their response, manifest and policy backing. Missing/corrupt,
expired, revoked or incompatible state returns no eligible checkpoint. This is a
read-side refusal, not a deletion/repair worker or automatic network recovery.

A 304 must name the original committed 200, match source, requested/final URLs and
redirect representation, use the stored validators and arrive chronologically
after the prior successful check. It cannot point at another 304. Update only
check time and returned validators (retain prior values when absent); keep the
200/manifest anchor. Record the 304 and its immutable checkpoint association in the
same transaction. Do not add item observations, bytes, hashes or publication dates.
An exact 304 replay rechecks its backing and historical check chain, and cannot
rewind newer validators or check time.

Unknown `Vary` fields or `*` disable conditionals; supported names are User-Agent
and Accept-Encoding, bound by the request-variant ID. A no-store cache directive
blocks full-text storage/reuse pending policy review. All HTTP semantics are offline
record checks here, not transport behavior, request permission or proof of truth.

## Limits and review boundaries

D027 RSS response/aggregate 6 MiB, per-article 1 MiB and generic/catalog 8 MiB
bounds remain enforced by existing models; actual BLOB counts/hashes are checked
again at storage boundaries. The 2 GiB live-store ceiling, 512 MiB/day transfer and
$0 paid-service budgets remain unchanged. Comprehensive filesystem/WAL/headroom,
encryption, backup/purge and operational lifecycle enforcement remain M1-04/B2
gates. No production path, real source body or runtime service is used or approved.
Issue #10 stays open for separate B1 measurements.

Tests must prove reopen/replay, source isolation, A→B→A and transform history,
same-key conflicts, corrupt/missing backing, policy/retention and 304 rejection,
foreign-key failures, rollback after writes, unchanged schemas/caps and no network.
Temporary database bytes and exceptions must never be printed or committed.

## API and review notes

`SQLiteEvidenceStore(path)` requires an explicit private file path; tests use
pytest temporary directories. `set_policy` selects an immutable supplied policy
assertion for offline evaluation, without activating a source. `commit_batch`
accepts a complete manifest, evidence bundles, artifact-ID-to-bytes mapping,
observations and an aware `at` timestamp. `record_not_modified` requires the
current `CheckpointContext`; `record_failure` never advances a checkpoint.
`get_checkpoint` returns only eligible state, otherwise None for invalid backing.
`get_artifact` evaluates policy and availability in one read snapshot.
`record_availability` appends an assertion; it performs no purge or restoration.
Internal `get_evidence`/`get_retrieval` metadata reads do not assert body access
or rights. Operational metadata retention/deletion remains M1-04 work.

Storage exposes bounded `StoreError` codes, suppressing raw SQL/validation error
text that could contain evidence. It logs no payloads. SQLite locks serialize
writers; a lock timeout rejects the transaction without advancing state. No
background retries, connection pool, migration engine or lifecycle workers exist.
The additive V2 API does not implement the legacy V1 `get`/`add` protocol; that
whole-M1 backend target stays deferred. Schema bindings and this API separation
are review choices, not changes to existing serialized core contracts.
