# M1 implementation readiness and PR execution plan

Review version: **1.0**, 2026-11-18. Target: **M1 specification v1.1, proposed**.
Verified main: `50224b35c1b27bbaca0fb1551bdf4b8205cb7de8`, the merge of
[PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4). No subsequent main
commits or open PRs were found at review start. The working tree was clean.
No source endpoints or vendor content were fetched during this review.

**Verdict:** the foundation can support a small offline contract increment once
explicitly approved. M1 as a whole is not implementation-approved or ready for
live operation. PR #4 accepted the documentation coordination baseline, not D004–D008
or collector implementation. Proposed corrections below require owner review.

## Decision review and precise corrections

| Finding in v1.0 | Proposed correction and impact | Decision / gate |
| --- | --- | --- |
| D004: vendor summaries may be retained while complete RSS bodies are snapshotted; a feed can embed full articles | Keep vendor sources disabled unless permission covers the entire retained representation and backup lifetime. Otherwise propose a metadata-only contract separately; do not strip a feed and call it exact evidence or invent an excerpt. Synthetic development does not depend on vendor rights. | D017; before vendor verification/activation |
| D005: replacing FetchedDocument or adding fields to strict V1 records would break callers/serialized data | Add independent versioned retrieval/observation contracts; keep every existing V1 shape and protocol signature unchanged in the first PR. Introduce a new fetch-result interface only in a later reviewed adapter integration. | D011; first PR |
| A 304 has no new body, yet the plan requires body metadata and observations | Model 304 separately, linking directly to a committed 200 response for the same source/representation. Record a check, not fresh per-item observations or fabricated publication/retrieval content. | D011; first PR plus storage tests |
| Content-derived IDs exclude retrieval time, but immutable SourceItem embeds retrieved_at | Keep the originally committed V1 evidence snapshot on an unchanged revision. Store subsequent retrieval times/locators in separate observations; never submit a different snapshot under the old evidence ID. | D012; identity/storage |
| A→B→A content reuse plus predecessor links inside immutable evidence can conflict or create cycles | Reuse content revision A and append a chronological observation. Leave parent_evidence_ids for genuine derivation, not temporal succession. History is ordered observations, not a mutable predecessor graph. | D012; identity/storage |
| Separate snapshot files and SQLite need a two-resource recovery protocol | For this bounded MVP, propose snapshot BLOBs in the same private SQLite database, keyed by digest. Commit snapshots/evidence/observations/checkpoint in one transaction. Defer external snapshot files and orphan reconciliation. This explicitly revises D005's separate-directory proposal. | D013; storage approval |
| Partial feed acceptance can advance validators past rejected entries; reprocessing/304 behavior is unclear | Reject the entire source batch on any invalid entry, retain the previous processing checkpoint, record safe failure metadata, and continue other sources. No item quarantine/replay subsystem in M1. | D015; parser/runner |
| D008 offers DNS pinning or egress filtering, but no selected connection/proxy behavior | Propose direct-only transport on a separately approved host: connect to validated resolved IP while retaining original TLS hostname/SNI, no automatic redirects, disable inherited proxies, revalidate every hop/retry. If the chosen client cannot prove this, transport is not ready. No proxy fallback or bypass of the current environment's restrictions. | D014; transport implementation design and live gate |
| D008 leaves total retry timing, encodings, depth and header limits open | Set a 180-second per-source wall budget including backoff/redirects/fallback, three top-level attempts maximum, within the 10-minute run budget. Propose UTF-8 only, maximum nesting depth 64, and response headers ≤32 KiB. Retain byte/item/text caps from M1. | D015; transport/parser |
| D006/Gate B requires runtime checks before any live run, while the pilot is needed to obtain them | Separate B1 authorized bounded verification from B2 approved manual collection. Both need explicit source-specific approval; Gate C separately enables recurrence. Offline contracts/storage need neither a production host nor source access. | D016; approval sequencing |
| D007's 365-day retention, 2 GiB cap and seven backups lack a capacity/rights reconciliation | Keep the cap as a stop condition, not a promise of year-long capacity. At 12 MiB of changed snapshots/day, 365 days exceeds 4 GiB before indexes. Measure the approved pilot, choose storage/retention with rights, and stop before limits rather than auto-delete cited data. Include backups in expiry/deletion policy. | D017; before live collection |

D004–D008 remain proposed, with these refinements; no earlier decision is silently
marked accepted. D009's TLP inheritance xfail remains an explicit exporter blocker.
Do not combine F5-wide validation hardening, F6 type-checker adoption, reporting
limits, or unrelated cleanup with the first increment.

## First PR specification: M1-01, core metadata contracts only

Suggested title: **Add versioned retrieval and observation contracts with synthetic fixtures**.
Prerequisite: explicit approval of **M1-01 under M1 v1.1 and D011**. No approval
for SQLite, HTTP, parsers or adapters is implied by approving this increment.

Scope: one additive module under `core/`, synthetic JSON fixtures and focused
tests, plus contract/status documentation. Use existing Pydantic and the standard
library only; no dependency, workflow, CLI, network or filesystem behavior changes.
The existing `models.py`, Collector/FetchedDocument/EvidenceRepository signatures
and V1 fixtures remain compatible. New record types have their own `kind` and
`schema_version: "1.0"`; the milestone document version is not a schema version.

Proposed data-only types (names may be refined in review without broadening scope):

| Type | Required information and invariants |
| --- | --- |
| `SnapshotRef` | Lowercase 64-hex SHA-256 of exact HTTP entity bytes after Content-Encoding decoding, before text/XML/JSON decoding; strict integer byte count 0–8 MiB; bounded media type. Digest reference only, never raw bytes or a storage path. RSS's stricter 2 MiB policy is enforced at its future boundary. |
| `ReceivedResponse` | Unique caller-supplied retrieval ID, source ID, exact requested/final HTTPS URLs, followed redirect destination tuple (max three), aware start/end times, status exactly 200, snapshot reference and optional returned ETag/Last-Modified strings. Transport success does not imply parsing success or checkpoint advancement. |
| `NotModifiedResponse` | Same attempt metadata, status exactly 304, nonempty sent ETag or Last-Modified, and required `representation_retrieval_id` naming the committed 200 result. Optional returned validators. No snapshot/body field; unknown fields reject. Storage later validates same source, endpoint/representation and existing digest. |
| `RetrievalFailure` | Retrieval/source/request identity, aware start/end times, optional received HTTP status (100–599), finite safe error code and retryability. Preserve a received 200/304 status when transport validation subsequently fails; `kind`, not status alone, distinguishes failure. No payload, raw exception text or success snapshot. Parser/storage failures are separate processing outcomes, not fabricated transport failures. |
| `EvidenceObservation` | Caller-supplied observation ID, current 200 retrieval ID, existing/new evidence ID, nonempty source-item locator and adapter version. It links an actual parsed representation to evidence. No per-item observation is created from a 304; its link to the original representation answers which evidence was checked. |

Shared metadata rules: IDs are UUIDs; source IDs 1–256 nonblank characters;
URLs ≤4,096 characters, HTTPS only, no userinfo/fragment/control characters,
preserved verbatim (syntax validation is not SSRF enforcement); validator strings
≤1,024 characters and no CR/LF; media type ≤128, locator ≤4,096, adapter version
≤128. New types are frozen, reject extras/unsupported versions and validate copy
updates. Explicit-offset timestamps only; reject integer epochs and naive times;
end must be at/after start. A redirected final URL equals the last followed
destination; without redirects it equals the requested URL. Later transport must
refuse unapproved redirect targets; this schema cannot prove network safety.
No operation ID or timestamp is generated as a side effect of constructing these
records. Unknown real publication dates never enter these transport records.

Proposed failure codes: `timeout`, `connection_error`, `tls_error`, `unsafe_url`,
`redirect_limit`, `proxy_disallowed`, `header_limit`, `body_limit`,
`content_decoding_error`, `http_error`, and `protocol_error`. The first PR validates
this vocabulary and a strict boolean retryability field; later transport decides
retryability under D015. A 200 whose body exceeds the cap is a `body_limit` failure,
not a complete ReceivedResponse. ReceivedResponse must be complete before parsing.

Use a discriminated union for the three retrieval outcomes. Cross-record
references are deliberately **not** claimed validated by standalone schemas:
transactional storage must enforce their existence, source/representation match,
and a 200 result for observations/304 targets. A received 200 can still have a
failed processing event; that must not become an eligible conditional checkpoint.

Acceptance tests for M1-01:

1. All existing V1 fixtures round-trip without changed shapes/defaults; existing
   test outcomes remain green, including the single explicitly known F4 xfail.
2. Synthetic 200/304/network-failure and observation JSON round-trip through their
   discriminated types. HTTP 429/503 failures and a 200 body-limit failure preserve
   safe status/code without body; unknown codes/statuses reject.
3. Reject 304 without a validator/reference, a body on 304/failure, mismatched
   kind/status, unsupported versions, unknown fields and invalid IDs/digests.
4. Reject malformed/credential/control-character URLs, redirect/final mismatch,
   naive/numeric or reversed times, booleans/negative byte counts, and values just
   beyond each metadata limit; accept exact-boundary values. No URL is fetched.
5. Invalid shallow/deep copy updates fail; valid copies preserve originals.
6. Keep core independent of collectors/storage and import-time side effects;
   all new tests run with the existing network block and use fabricated data only.

Do not implement revision generation, content hashing of fetched payloads,
checkpoint mutation, body storage, DNS resolution, adapters or retry loops here.
Snapshot digests and cross-record IDs in fixtures are synthetic test inputs, not
claims that retrieval or storage happened. A storage backend remains substitutable.

## Identity and transaction rules for subsequent increments

**D012, proposed identity profile v1:** distinguish operation IDs (caller-created
UUIDs, reused on retry of the same storage operation) from source item/revision IDs.
Freeze three UUIDv5 namespaces derived from UUID NAMESPACE_URL and repository
identity URLs ending `/identity/v1/logical`, `/source-item`, and `/evidence`.
Commit the exact namespace constants and test vectors in M1-02; never derive them
from the current checkout/branch or mutable source endpoint. Logical keys encode
`[source_id, native_id]` with no whitespace stripping/case folding; a missing GUID
uses the exact original article URL. Missing both is invalid, not a random ID.

Revision digest input is canonical UTF-8 JSON: sorted object keys, compact
separators, Unicode preserved, non-finite numbers forbidden, arrays in source
order. Include a profile version plus the source-field projection (title, exact
excerpt, publisher, original URL, original publication text/precision and relevant
source metadata); exclude retrieval time/URL, array position/locator, cache headers
and catalog release metadata. Each adapter must publish its exact field projection
and golden vectors before integration. Source-item/evidence IDs derive from
logical ID, profile version and revision digest using their distinct namespaces.
Parser changes that change meaning require a new profile, not mutation of old rows.

On a repeated revision, retrieve and reuse its existing immutable evidence,
including first committed retrieved_at; add the new observation/locator only.
On A→B→A, reuse A and append the observation without editing A's parent IDs.
Do not infer a retraction from a rolling RSS window. No automatic cross-source
merging or CVE-level attribution. This is normalization identity, not analyst work.

**D013, proposed storage:** use SQLite snapshot BLOBs to remove the filesystem/DB
commit split. Compute/check the digest before inserting; unique digest/content
must agree. Parse and validate the complete bounded source batch before the write
transaction. With foreign keys on and explicit durable commits, atomically write
snapshot, retrieval metadata, new revisions, observations, processing-success
event and next conditional checkpoint. Do not hold the transaction during network
I/O. A failure rolls back that batch; a separate small failure event may commit
without advancing its checkpoint. A crash before that event is allowed to leave
no event, but never a success checkpoint. Only one writer/run may operate at once.

A 304 may advance last-successful-check/returned validators only when the saved
200 representation was fully processed, still exists and matches the source and
request variant. Do not chain 304s as representation references. If its snapshot
is missing/corrupt, invalidate the conditional and consume a remaining attempt
on one unconditional fetch; no remaining budget means defer. An unsolicited 304
is a protocol failure. Checkpoints are scoped to endpoint and fixed request
representation headers; unexpected Vary fields disable conditional caching until
explicitly supported. No body parsing or new evidence on a valid 304.

Disk-full, constraint failure and injected crashes before/after COMMIT must
produce all-or-none source state. Retrying a committed operation ID is a no-op;
reuse with different contents rejects. Backups use a transactionally consistent
SQLite backup, not a blind copy of a live database file; restore verifies foreign
keys, snapshot hashes and checkpoint references. Schema version/migrations must
fail closed on unsupported versions; no destructive automatic downgrade.

## Ordered, independently reviewable PRs

Keep the requested stage order; split storage, transport/parsing and adapters
into smaller PRs. IDs below are execution-plan IDs, not preallocated GitHub PR numbers.
Each row requires explicit implementation approval covering it and its prerequisites;
a dependency being merged is not authorization to start the next row.

| Increment | Dependencies | Narrow deliverable and acceptance tests |
| --- | --- | --- |
| M1-01 Core metadata | Gate A limited to this row / D011 | Types and synthetic fixtures above; reject invalid combinations and preserve V1. No new dependencies. |
| M1-02 Identity profile | M1-01, approval of D012 | Pure identity helpers/sidecar linkage contracts and frozen vectors. Same content with later retrieval/reordered object keys retains IDs; title/excerpt changes create revisions; sources/profile versions separate; A→B→A reuses A without cycles. No backend. |
| M1-03 SQLite atomic storage | M1-02, D013 approval | Temporary-database backend, BLOB snapshots, transactional batches/checkpoints. Replay no-op, content conflicts, foreign keys, invalid 304 reference, incomplete batch rollback; no live data or default production path. Standard-library SQLite only. |
| M1-04 Recovery and backups | M1-03 | Failure injection around COMMIT, full disk/read-only paths, unsupported schema, consistent backup/restore, corrupted/missing snapshot and 304 recovery signals, exclusive run lock. No timer or operational backup job. |
| M1-05 HTTPS transport | M1-01, D014/D015 design approval | Injected resolver/connection/clock; prove DNS-to-socket binding, TLS hostname checking, redirects, mixed/special IP ranges, proxy rejection, header/byte/deadline limits and conditional outcomes using fakes. Pin one chosen client only if needed. No public endpoint calls. |
| M1-06 Safe parsing | M1-01, D015 approval | Pure bounded JSON/RSS parsing helpers and at most one hardened XML dependency. Synthetic entity/DTD/depth/encoding/oversize/empty/malformed tests; HTML remains inert; no storage or transport imports. |
| M1-07 CISA adapter | M1-02, M1-05/06 | Synthetic catalog/schema fixtures; CVE identity, date-only precision, optional fields, duplicates, count mismatch, reordered entries and changed descriptions. Test injected fetch/parse independently; no KEV requests. |
| M1-08 Microsoft adapter | M1-02, M1-05/06 | Synthetic RSS GUID/URL fallback, missing summary/date, literal HTML, exact attribution and source projection vectors. Rights unresolved means disabled; no vendor fetch/fixtures. |
| M1-09 Google adapter | M1-02, M1-05/06 | Independent synthetic mapping for publisher/entry links and possible tracking/original-link extensions; absent/unverified extensions do not trigger fetches or guessed URLs. Disabled; no vendor content. |
| M1-10 Manual CLI / offline integration | M1-04, M1-07/08/09, D015 | Static composition, source budgets, safe diagnostics, injected end-to-end fetch→store tests, one failing source leaves others successful, no checkpoint on invalid batch, 304/restart paths, redacted logs and disabled-by-default live mode. Narrow composition-layer import exception. |
| M1-11 Source verification / manual activation | M1-10 plus separate B1/B2 approvals and D017 | CISA first, only once authorized; vendor content requires prior collection/retention basis. Source-specific requests/byte budget, private operator/host, robots/TLS/redirect/cache evidence, recovery/backup and permissions review. No automation; three-source completion still requires all three or an approved scope revision. |
| M1-12 Recurring scheduling | Successful approved manual pilot, Gate C | Separately reviewed timer/runbook, no overlap, one missed-run catch-up, stale-source and disable/restore tests, operator/capacity/backup checks. No schedule is created by earlier increments. |

For all implementation increments: Ruff check/format and offline pytest must pass
on supported CI versions; preserve the F4 xfail until an explicitly approved fix.
No later-stage behavior, paid services, live access or permanent data is part of
M1-01 through M1-10. Test databases contain only synthetic records and are temporary.

## Approval request and stopping point

Recommended exact first approval:

> Approve M1-01 only under M1 specification v1.1 and proposed D011: additive,
> versioned retrieval/observation metadata contracts, synthetic fixtures, focused
> offline validation tests, and related contract/status documentation. Preserve
> existing V1 contracts and protocol signatures. No collectors, persistence,
> transport, parsing implementation, live requests, scheduling, deployment,
> new dependencies, or paid services are authorized by this approval.

This is requested wording, **not an approval already given**. Record the owner's
actual approval and reference before writing application code. D012–D017 and
D004–D008's operational choices remain proposed/open for their later increments.
Private host/operator, rights-dependent retention (including backups), network
path/client choice, parser budgets and capacity are unresolved for live readiness.
No vendor content may be fetched or archived now. The handoff remains
[STATUS.md](../STATUS.md) plus the permanent [HANDOFF.md](../HANDOFF.md) procedure.
