# M1 implementation readiness and PR execution plan

Review version **1.1**, 2026-11-18. Target: **M1 v1.2, proposed technical design**.
Verified main: `1e5c2bca28077406acae576b88e77114f1288450`, the merge of
[PR #5](https://github.com/Ih4c/ghana-cti-pipeline/pull/5). PR #4 and #5 merges
were verified in Git and GitHub; no later main commit or open PR existed at this
review's start, and the working tree was clean. Neither merge approved code.
No source endpoints or vendor content were fetched during this review.

**Verdict:** the owner's hybrid strategy is accepted (D018); the technical design
and all implementation increments still require approval. The first small offline
retrieval/observation increment remains appropriate, with receipt descriptors that
do not imply raw retention. See [M1_EVIDENCE.md](M1_EVIDENCE.md) for the proposed
source policies, V2 representation, conditional requests and reporting assessment.

## Corrections to the v1.1 proposal

| Prior assumption / gap | Proposed correction | Decision |
| --- | --- | --- |
| Every 200 has a SnapshotRef that appears to imply archiving | Use a response-body descriptor for observed size/media/digest; retention association is separate and occurs only at validated commit. | D011/D019 |
| Vendor retention requires complete feed archival permission or deferral | Accepted metadata-first direction; require permissions for bounded transient parsing and specifically retained fields. No raw vendor archive by default; metadata is not automatically exempt. | D018 accepted; D017/D020 proposed |
| V1 mandates an exact excerpt | Keep V1 unchanged. Add a distinct versioned V2 evidence representation later; absent excerpt is honest and valid only there. | D019 |
| 304 requires a retained raw snapshot for all sources | Require the committed 200 processing manifest and retained projections; require a raw artifact only for raw-backed mode. A 304 never reprocesses unretained bytes or renews rights. | D019 |
| Full-response identity suggests full article change tracking | Item identity uses allowed retained projection/profile; track response digests separately. Metadata equality cannot establish article equality. | D012 |
| One retention period / seven backups seems sufficient | Require per-source/per-class deadlines including hashes, policy metadata and backups; verify deletion outside active SQLite rows and isolate restores. | D017/D020 |
| Metadata supplies report-ready evidence | Metadata supports discovery/citation and limited listing facts. Article-level claims need human verification and permitted support/corroboration. The authoritative template remains unchanged; actual template is not in the checkout. | D018/D021 |

Keep the v1.1 improvements: immutable observations, A→B→A reuse, source-batch
atomicity, SQLite BLOBs for permitted raw acquisitions, direct-only validated-IP
transport, safe parsing limits, source budgets and separate approval gates.
Do not bundle F5-wide V1 validation changes, F6 tooling, TLP inheritance resolution,
reporting implementation or unrelated cleanup into the first increment.

## M1-01: offline retrieval and observation descriptors only

Prerequisite: explicit owner approval of **M1-01 under M1 v1.2 / D011 and the
retrieval/observation portion of D019**. No V2 evidence implementation, storage,
network or parser approval is implied. Suggested title: **Add retention-neutral
retrieval and observation contracts with synthetic fixtures**.

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

## Dependency-ordered implementation PRs

Execution-plan IDs are not GitHub PR numbers. Preserve the requested order;
split old M1-02 into M1-02a evidence contracts and M1-02b pure identity so each is
reviewable. No implementation exists for either old or new plans. Each row needs
explicit Gate A approval covering its scope and listed decisions, in addition to
merged dependencies. Approval may name several rows; a merge alone approves none.

**Common constraints for M1-01 through M1-10:** synthetic fixtures, blocked real
network, private temporary test data, no production paths or source access, no
paid services, deployment, scheduling, publication, reporting/template changes or
later-stage behavior. Existing V1 compatibility and CI Ruff/pytest are required.
Only transport/XML rows may propose minimal reviewed open-source dependencies.
Source permissions stay unresolved until documented; no test source is a license.
The per-row exclusions below add to these common exclusions.

| Increment / components | Dependencies and owner approval | Scope and acceptance tests | Security/rights constraint and exclusions |
| --- | --- | --- | --- |
| M1-01 Core descriptors; `core/`, fixture/tests, contract docs | Gate A: revised D011 and descriptor portion of D019 | Types/tests above, explicitly no retention claim | No V1 changes, new dependencies, V2 evidence or I/O |
| M1-02a Hybrid evidence; `core/`, synthetic fixtures/tests | M1-01; Gate A: D019 evidence design and D020 policy-reference semantics | Add V2 modes/provenance, optional permitted excerpt object and policy/manifest/availability contracts. Test absent excerpt valid only for V2, mode/artifact contradictions, date precision, bounded allowlisted fields, unknown defaults and version dispatch. | No inferred permissions, catch-all vendor fields, V1 migration, backend or hashing helpers |
| M1-02b Identity; `core/`, tests/vectors | M1-02a; Gate A: revised D012 | Pure canonical projections/UUID namespaces and digest helpers. Freeze exact namespace constants and vectors. Source/key-kind/profile separation, key ordering, changed retained fields, A→B→A, ignored article-body changes and policy-renewal stability. | No cross-source merging, article equality claims, tombstone resurrection or I/O |
| M1-03 SQLite; `storage/`, protocols, temporary-store tests | M1-02b; Gate A: revised D005/D013/D019 | Both transaction shapes, manifest/checkpoint eligibility, versioned lookup, typed writes; 304 succeeds for valid metadata-only state without raw body, fails for missing required raw backing; replay/conflict/rollback/FK tests. | Metadata-only API rejects raw bytes/artifact association and policy mismatch. No production DB, CLI, live data or raw vendor retention |
| M1-04 Recovery/lifecycle; `storage/`, tests, runbook docs | M1-03; Gate A: D017/D020 and concrete purge/restore design | COMMIT crash/disk-full/read-only/schema tests; consistent backups; isolated restore; expiry/deletion invalidates references/checkpoints; permitted tombstones; synthetic marker absent from metadata DB/WAL/backups; corruption and locking. | No operational backup job; no secure-erasure claim from SQL DELETE; real-host purge verification remains B1/B2 gate |
| M1-05 HTTPS; `collectors/` transport helpers, tests | M1-01; Gate A: D008/D014/D015 transport/client design | Fake resolver/socket/clock: IP pinning with original-host TLS, DNS rebinding, all redirects/retries, mixed special IPs, proxy rejection, byte/header/time budgets, conditionals and no disk cache/spool. | No real endpoint requests, implicit proxy fallback or debug body capture; at most one justified HTTP client dependency |
| M1-06 Safe parsing; `collectors/` pure parser helpers, tests | M1-02a; Gate A: D015/D019 projection rules | Synthetic JSON/RSS entity/DTD/depth/encoding/size/item tests; full content:encoded/description discarded by default; permitted exact excerpt selection, invalid dates flagged, forbidden marker never returned in projection/error. | Transient bounded buffers only, no I/O, storage/transport imports or HTML execution; at most one hardened XML dependency |
| M1-07 CISA adapter; separate collector module/tests | M1-02b, M1-05/06; Gate A: D004 CISA mapping | Synthetic catalog counts/duplicates/reordering/changed fields, original dates/fields, raw-backed locators and digest linkage; fetch/parse independently injected | CC0 basis applies to catalog only; no linked downloads, request, or activation |
| M1-08 Microsoft adapter; separate collector module/tests | M1-02b, M1-05/06; Gate A: D004 vendor mapping/D017 | Synthetic GUID/URL fallback, missing summary/date, metadata-only output, optional policy-permitted exact excerpt, source projection vectors, full article marker excluded on success/error | Disabled pending rights; no real vendor fixtures, raw storage or article requests |
| M1-09 Google adapter; separate collector module/tests | M1-02b, M1-05/06; Gate A: D004 vendor mapping/D017 | Independent synthetic mapping, publisher/final/article URLs, verified extension handling, same absent-excerpt/leak tests as Microsoft | Disabled; no guessed original links, tracking requests, premium API or raw archive |
| M1-10 Manual CLI; composition/CLI, offline integration tests | M1-04, M1-07/08/09; Gate A: D006/D015/D019/D020 | Static composition, two modes end-to-end, one source failure isolation, 304/restart/expiry, source budgets, safe diagnostics; injected secret/forbidden-content canaries absent from DB/backups/logs; default live mode disabled | Narrow import-boundary exception only for composition; no acquisition through CLI until B2, no timer or external messages |
| M1-11 Verification and manual pilot; source-policy/runbook/feasibility docs | M1-10; separate B1 per-source verification approval, then B2 activation; D004/D007/D017/D020 | CISA first; bounded approved requests verify TLS/redirects/cache/fields/limits/robots. Verify permitted data, host dump/swap/backup/purge behavior, then manual pilot and repeat/304 per cleared source. Document counts/growth and gaps privately. | Vendor transient-processing/metadata/excerpt rights basis required before requests. No raw vendor evidence upload, article scrape, automatic activation or schedule. Three-source completion requires all three or explicit revised scope |
| M1-12 Scheduling; operator runbook and separately reviewed timer | Approved successful manual pilot; Gate C/D006/D007 | No overlap, one missed-run catch-up, expiry/stale-source pause, safe shutdown/restore, capacity/operator checks | Existing approved private host/budget only; no source expansion, paid services or publication |

D012 namespace design: derive fixed UUIDv5 namespaces from NAMESPACE_URL and
repository identity URLs with versioned logical/source-item/evidence suffixes;
commit exact constants/vectors in M1-02b, never derive from branch or checkout.
Use canonical UTF-8 JSON, sorted keys, compact separators, preserved Unicode and
array order, no non-finite numbers. Exact retained-field projections and null/absent
semantics must be frozen per adapter/profile. See [hybrid identity rules](M1_EVIDENCE.md).

## Remaining decisions and exact next approval

D011/D019 descriptor details need owner approval for M1-01. Later gates include
V2/projection and identity semantics, SQLite protocols and purge/restore procedure,
HTTP client/IP binding, source-specific transient/retained rights and deadlines,
private host/operator, memory/dump controls, backups and measured capacity. D021's
template artifact/license and claim-level verification gaps block later report
tooling, not synthetic M1-01. D009 TLP inheritance still blocks any exporter.

Requested scope, **not approval already given**:

> Approve M1-01 only under M1 v1.2, revised D011 and the retrieval/observation
> descriptor portion of D019: additive core metadata contracts, synthetic fixtures,
> focused offline validation tests and related contract/status documentation.
> Preserve existing V1 shapes/protocols; add no dependencies. Exclude V2 evidence
> implementation, persistence, hashing behavior, transport, parsers, adapters,
> live requests, deployment, scheduling, paid services and reporting/publication.

Record actual owner approval before code. Until then, only documentation review
is authorized. The permanent [handoff procedure](../HANDOFF.md) remains reusable;
[STATUS.md](../STATUS.md) carries current work and blockers.
