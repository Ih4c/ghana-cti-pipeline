# M1 implementation readiness and PR execution plan

Review **1.2**, 2026-11-19. Target: **M1 v1.3 full-text proposal**.
Planning baseline was PR #6's merge. PR #7 subsequently merged this review at
`3c257a6f05ff5c5aaf7968aa8df50ca26f3349c7`, verified 2026-11-19.
The older unfinished local v1.2 draft remains preserved separately.
No source requests or new runtime/terms verification occurred.

D022 accepts full-text collection as the strategy; D023 records risk acceptance,
not rights clearance. The [owner approval on PR #7](https://github.com/Ih4c/ghana-cti-pipeline/pull/7#issuecomment-6996754396) subsequently authorizes only
M1-01 under v1.3. See [STATUS.md](../STATUS.md) for implementation review state.
Subsequent [M1-02a approval](https://github.com/Ih4c/ghana-cti-pipeline/pull/8#issuecomment-6997113844)
covers D019/D024 data contracts only. PR #15 separately approves M1-02b helpers,
delivered by PR #16. The [PR #16 owner comment](https://github.com/Ih4c/ghana-cti-pipeline/pull/16#issuecomment-7108040658)
approves M1-03 offline SQLite persistence and synthetic temporary-database tests.
The [PR #17 owner comment](https://github.com/Ih4c/ghana-cti-pipeline/pull/17#issuecomment-7119143529)
subsequently approves M1-04 offline recovery/lifecycle and capacity checks. The
[PR #18 owner comment](https://github.com/Ih4c/ghana-cti-pipeline/pull/18#issuecomment-7119629449)
approves M1-05 standard-library HTTPS transport with injected fakes only. M1-06a
onward and operational gates remain pending.

The subsequent [D027 owner decision](https://github.com/Ih4c/ghana-cti-pipeline/issues/10#issuecomment-7008185129)
approves only the 6 MiB RSS response/representation-aggregate amendment and synthetic
boundary tests. Keep 1 MiB per article and generic 8 MiB limits. B1 measurement
does not block this numeric change, but remains required to confirm headroom;
no source access, new runtime components or operational gate is approved.

## Changes affecting readiness

| v1.2 assumption | v1.3 proposal / consequence |
| --- | --- |
| Vendor metadata is the intended deliverable | Complete Microsoft content:encoded and Google description bodies, as owner-reported on 2026-11-18; independent B1 confirmation and lawful basis required. Missing/truncated fields block full-text completion, not a silent fallback. |
| Raw vendor bytes cannot enter persistent storage | Authorized full-text originals and derivatives belong in the approved private store; public/log/CI leakage remains forbidden. Source permissions, encryption and deletion controls govern every copy. |
| Metadata-only 304 can omit raw backing | Current full-text target requires intact permitted original/derived artifacts and manifest. Corruption invalidates checkpoint; rights expiry pauses, without automatic re-fetch. |
| Article changes may be invisible to metadata identity | Original selected body participates in source revision identity. Sanitizer changes create linked immutable derivatives; do not overwrite originals or historical transforms. |
| No HTML transformation capability needed | Separate pure sanitization/text-extraction increment, D024. Retain original feed field, sanitized HTML and plain text with independent hashes/parents/versions. No rendering, resource loads or article crawling. |
| Storage volume is mostly CISA plus metadata | Full-text/derived budget up to 64 MiB/day before overhead, versus unchanged 2 GiB cap. Capacity/retention choice is a live gate, never implicit expansion. |
| Daily polling versus retry/recovery unclear | One automatic cycle per source/24 hours; attempts, redirects, restart and recovery share persisted budgets. Publisher limits can be stricter; 403 pauses, 429 defers. |

The [evidence/rights design](M1_EVIDENCE.md) supplies precise proposed fields,
transforms, hashes, retention and 304 rules. Keep modularity, V1 compatibility,
source isolation, SSRF/TLS/proxy rules and human reporting controls. D009 TLP
inheritance remains open. No F5-wide cleanup, F6 tooling or report implementation.

## M1-01: offline retrieval and observation descriptors only

State: **delivered by PR #8**, merged at `9e30ab5a3d88352f97fd7fa64ea2a676097e0e72`.
The owner comment above approves **M1-01 under M1 v1.3 / D011 and the
retrieval/observation portion of D019**. No V2 evidence implementation, storage,
network or parser approval is implied. Implementation title: **Implement M1-01 retention-neutral retrieval and
observation contracts**.

Scope: one additive module under `core/`, synthetic JSON fixtures, focused tests
and contract/status documentation. Existing `models.py`, V1 fixtures and
Collector/FetchedDocument/EvidenceRepository signatures stay unchanged. Existing
Pydantic and standard library only; no dependencies, CLI, workflow or I/O changes.
New record types use a distinct `kind` and their own `schema_version: "1.0"`;
this is unrelated to the milestone version or later EvidenceRevisionV2.

| Proposed data-only type | Information and invariants |
| --- | --- |
| `ResponseBodyMetadata` | Complete decoded-entity byte count and transferred byte count (strict integers 0–8 MiB), bounded media type/content encoding; `digest_state: computed/not_computed`. Computed requires lowercase 64-hex SHA-256 and domain `decoded-http-entity-v1`; not_computed requires digest null. No bytes, path, artifact ID or retention flag. RSS's tighter cap is enforced at its future boundary. |
| `ReceivedResponse` | Caller-supplied UUID retrieval ID, source ID, exact requested/final HTTPS URLs, followed redirect destinations (max three), aware start/end times, status 200, body descriptor, optional returned ETag/Last-Modified and bounded Cache-Control/Vary metadata. Receipt does not mean valid parsing, retained body or successful checkpoint. |
| `NotModifiedResponse` | Same attempt metadata, status 304, at least one nonempty sent ETag/Last-Modified, required direct `representation_retrieval_id` naming the processed 200; optional returned validators/Cache-Control/Vary. No body descriptor, new body digest, snapshot or artifact. Storage validates manifest/source/variant/mode/rights later. |
| `RetrievalFailure` | Retrieval/source/request identity, aware start/end times, optional received HTTP status 100–599, finite safe code and strict boolean retryability. Preserve received 200/304 status if transport validation fails afterward. No body, partial-body digest or arbitrary exception text. Processing/storage failures remain separate. |
| `EvidenceObservation` | Caller-supplied UUID observation ID, current parsed-200 retrieval ID, evidence ID plus kind/version (`v1`/`1.0` or `hybrid`/`2.0`), nonempty locator, adapter version, source policy ID/version. This describes a link, not validation of an evidence object's existence or rights. A 304 creates no per-item observation. |

Shared limits: source/policy IDs 1–256 nonblank characters; version strings 1–128;
URLs ≤4,096, HTTPS, no credentials/fragments/control characters and preserved
verbatim; locator 1–4,096; media type/content encoding 1–128. Optional validator,
Cache-Control and Vary strings ≤1,024 and no control characters; absent values
are null, present values nonblank. Only these named HTTP fields are retained,
not arbitrary header maps, cookies, auth headers or raw header dumps. Runtime
must also enforce the 32 KiB aggregate header limit from M1. Reference/article
URL rules belong to the later evidence schema, not transport destination approval.

Types are frozen, extra-forbid, reject unsupported kinds/versions and validate
copy updates. UUIDs and times are caller-supplied; explicit-offset timestamps
only, no numeric epochs/naive values; end ≥ start. Final URL equals last followed
redirect or requested URL when no redirect occurred. URL validation is syntax,
not SSRF protection. Standalone records cannot verify cross-record references,
policy permission, digest computation, actual retention or network safety.

Failure codes remain `timeout`, `connection_error`, `tls_error`, `unsafe_url`,
`redirect_limit`, `proxy_disallowed`, `header_limit`, `body_limit`,
`content_decoding_error`, `http_error`, `protocol_error`. Later transport applies
retry policy; a capped 200 is a failure, not a complete ReceivedResponse.
Use a discriminated union for 200/304/failure; no hash calculation is implemented.

Acceptance tests:

1. Existing V1 JSON shapes/defaults round-trip unchanged; missing/blank V1 excerpts
   still reject. Baseline tests and the single tracked F4 xfail remain unchanged.
2. Synthetic 200 descriptors with/without digest, 304, 429/503 and 200 body-limit
   failures round-trip; observation links support both declared evidence versions.
3. Reject contradictory digest states, invalid hex/domain, unknown fields/codes,
   unsupported versions and raw body/path/artifact injection into any descriptor.
4. Reject 304 without validator/reference or with body/digest; invalid kind/status,
   mismatched evidence kind/version, bad UUIDs and malformed/credential URLs.
5. At-limit values pass; over-limit strings/redirects/byte counts, boolean/negative
   byte counts, control-character headers, numeric/naive/reversed times fail.
6. Invalid shallow/deep copy updates fail; valid copies leave originals unchanged.
   Core dependency checks and blocked-network tests remain green; no side effects.

Synthetic hashes/IDs are declared fixture values, not claims of actual retrieval.
Do not add evidence V2, revision generation, policy enforcement, hash calculation,
SQLite, checkpoint logic, DNS, transport, parser, adapter or retry behavior here.

## M1-02a: full-text evidence contracts

State: **delivered by PR #9 (approved data-only scope)**.
The owner comment above names M1 v1.3 and D019/D024. See the
[contract reference](../M1_EVIDENCE_CONTRACTS.md) for concrete wire fields/limits,
synthetic tests and remaining cross-record/rights boundaries. D025 records wire bindings delivered by PR #9; D026 records the source-revision/derivation identity gap
resolved by the M1-02b profile below. M1-01/V1 serialized shapes remain unchanged.

## M1-02b: deterministic identities and digests

[Owner approval on PR #15](https://github.com/Ih4c/ghana-cti-pipeline/pull/15#issuecomment-7008787831)
covers D012/D024 pure helpers and D026 resolution under v1.3. The
[profile specification](../M1_IDENTITY_PROFILES.md) fixes original source projections,
separate derived/association keys, namespaces, canonical JSON and digest domains.
Synthetic tests cover A→B→A, transform independence, exact source-key boundaries,
Unicode, fixed vectors, supplied-record consistency, immutable copies and no I/O.
Existing contracts, D027, per-article caps and the TLP xfail stay unchanged.

## Revised dependency-ordered PRs

Every increment requires separately recorded owner approval naming its version
and scope; dependency merges alone grant none. M1-01 remains a small offline
contract PR; its [contract reference](../M1_RETRIEVAL_CONTRACTS.md) documents
the implementation. M1-02a is delivered by PR #9 and D027 by PR #15; neither
implies source rights. M1-02b stops at its independent implementation review PR.

Common constraints for M1-01 through M1-10: synthetic fixtures, blocked real
network, temporary test stores only, no real source bodies or production paths,
no paid services/deployment/scheduling/publication, no template/report changes,
and unchanged V1/protocol compatibility. CI Ruff/format/pytest remain required.
Later HTTP/XML/HTML dependencies must be minimal, open source, reviewed and pinned.
Each row lists additional scope/tests/exclusions; M1-01/M1-02a contracts and
M1-02b pure helpers are approved. Later increments remain separately gated.

| Increment / components | Prerequisites / approval | Scope and acceptance tests | Additional exclusions / rights boundary |
| --- | --- | --- | --- |
| M1-01 descriptors; core/fixtures/tests/docs | Gate A, v1.3 D011 and D019 descriptors via owner PR comment | Types and tests above; unchanged V1, immutable copies and digest-state discrimination | No dependencies, V2, hashing behavior or I/O |
| M1-02a full-text contracts; core/tests | M1-01; D019/D024 artifact/derivation design approval | Proposed catalog_entry/feed_full_text V2, policy/availability/manifest and original/derived references; provenance, version/mode mismatch, missing full-text backing, dates and size bounds | No backend, transforms, hash computation or metadata-only completion |
| M1-02b identities/digests; core/vectors | M1-02a; D012/D024 approval | Fixed namespaces, canonical profiles and independent response/original/derived digest helpers; body changes, reordering, A→B→A, same sanitized output with changed original, transform-version changes | No cross-source merge, overwritten originals, deleted-record resurrection or I/O |
| M1-03 SQLite; storage/protocols/tests | M1-02b delivered; D005/D013/D019 offline scope approved on PR #16 | Atomic response/item/derived/manifest/observation/checkpoint store; policy-bound BLOB associations, conflicts/FKs/replay and rollback; valid 304 needs all required backing | Synthetic temporary DB only; no production paths or actual content |
| M1-04 recovery/lifecycle; storage/tests/runbook | M1-03 delivered; D007/D017/D020 offline scope approved on PR #17; D029 binding for review | Crash/disk-full/read-only/schema/locking tests, 2 GiB accounting/headroom, consistent backup, WAL/purge/expiry/revocation and isolated restore; all derived copies included | No operational backup job; no claim SQL DELETE proves erasure; real-host validation before B2 |
| M1-05 HTTPS; collectors transport/tests | M1-01 delivered; D008/D014/D015 offline scope approved on PR #18; D030 for review | Injected resolver/socket/clock proves IP pinning/TLS, rebinding, redirects, proxy rejection, headers/byte/time limits, descriptive UA, conditionals, 403 no-retry and Retry-After | No live HTTP, proxy bypass or automatic links; minimum approved client only |
| M1-06a parsing; collectors pure parser/tests | M1-02a; D015/D024 approval | Safe XML/JSON, UTF-8/conflicting encodings, DTD/entity/depth/count/size tests; exact complete source-field extraction, missing/truncated body failure and original response/field distinction | No HTML execution, storage/transport imports, live feeds or article requests |
| M1-06b transformations; collectors pure helpers/tests | M1-02b, M1-06a; D024 policy/library approval | Synthetic full HTML to separate original/sanitized/plain representations; independent hashes/parents/versions; active tags/attributes/resources, malformed/mutation-XSS, encoding/entity, node/attribute/aggregate limits, deterministic text and failure tests | No viewer/browser, rendering, embedded-resource fetch, AI summary or replacement of original; reviewed sanitizer/parser dependencies only |
| M1-07 CISA adapter; own module/tests | M1-02b, M1-05/06a; D004 mapping approval | Complete synthetic entry fields/catalog count/date precision, duplicate/conflict/reordering/change tests, locators and raw associations; no invented HTML representation | Catalog license scope only; no linked material or real requests |
| M1-08 Microsoft adapter; own module/tests | M1-02b, M1-05/06a/06b; D004/D024 mapping approval | Synthetic content:encoded namespace/full body, missing/truncated field fail, GUID/URL fallback, original/sanitized/plain association, dates/versions/provenance and failure isolation | Disabled until rights and B1/B2; no real fixtures, article crawler or metadata fallback |
| M1-09 Google adapter; own module/tests | Same as M1-08; independent D004 mapping approval | Synthetic description full body, source/publisher/final/original URL mapping and verified extension handling; same full-text/transform tests independently | No guessed URLs, tracking fetch, paid API, real content or fallback |
| M1-10 CLI/offline orchestration; composition/tests | M1-04, M1-07/08/09; D006/D015/D019/D020 approval | Static composition, full-source transactions, transform failure isolation, 304/reprocessing/restart, one cycle/24h with persisted shared budgets and stricter publisher rules; synthetic body canaries absent from logs/CI outputs | Only approved private storage may contain synthetic bodies; no live CLI use, default activation, timer or external messages; narrow tested import exception |
| M1-11 B1 verification then B2 manual pilot; policies/feasibility/runbook | M1-10; separate source-specific B1 and B2 approval, D017/D023 rights resolution, capacity/host sign-off | CISA first candidate; independently reconfirm reported feed fields/completeness, access/robots/UA/validators/limits and full-text rights. Verify host encryption/backup/purge, private artifact integrity and measured growth | Bound each approved request; prohibited/unresolved source mode blocked; no metadata substitution or public bodies. No recurring schedule |
| M1-12 scheduling; timer/runbook | Approved manual pilot; separate Gate C, D006/D007 | One automatic cycle per source/24h, no overlap/burst, persisted budgets, Retry-After/403 handling, expiry/stale checks, shutdown/restore/capacity/operator checks | Existing approved host/budget only; no source expansion, publication or paid services |

Exact UUID namespace constants and source/transform profile vectors must be frozen
before identity implementation: canonical UTF-8 JSON, sorted keys, preserved
Unicode/array order, explicit null/absent semantics, no non-finite numbers. IDs
must never depend on checkout/branch or mutable retrieval times. Source revision
and transformation lineage are distinct, as specified in M1_EVIDENCE.md.

## Blockers and stopping point

Full-text access/retention/derivation/backup rights and the reported RSS fields
remain unverified. Owner risk acceptance does not clear them. Source policies,
HTTP/sanitizer choices, transform budget feasibility, 2 GiB capacity/retention,
private host/operator, keys, purge/backup/restore and report-level rights need
review at their respective gates. Template artifact/license, evidence sufficiency
and D009 inheritance remain later reporting blockers.

**M1-01 through M1-04 are delivered; M1-05 offline HTTPS transport has separate
approval under v1.3.** M1-05 stops at independent review of the
[transport binding](../M1_TRANSPORT.md), injected-fake tests and documentation.
M1-06a needs fresh approval. No live DNS/HTTP, source registry/default endpoints,
robots/policy fetching, source parsing, sanitization, adapters, storage integration,
persisted retry budgets, deployment, schedule or publication are authorized.
Use the permanent [handoff procedure](../HANDOFF.md) and [STATUS.md](../STATUS.md).
