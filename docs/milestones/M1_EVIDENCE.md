# M1 hybrid evidence and source-retention design

Design version **1.0**, 2026-11-18; companion to [M1 v1.2](M1_COLLECTION.md).
D018 records the owner's accepted strategic direction. D011–D017 refinements and
D019–D021 below are proposed/open, not implementation or source-access approval.
No source content was fetched to prepare this design.

## Source-specific policy

| Source | Intended representation | Retain only after source approval | Excluded / unresolved |
| --- | --- | --- | --- |
| CISA KEV official catalog | Raw-snapshot-backed | Licensed catalog's original fields, bounded complete response, source provenance and normalized records; checked database CC0 basis in the feasibility log | Recheck applicable endpoint/access conditions. CC0 does not cover linked third-party material, logos or endorsement. No following links. Runtime checks/activation still pending. |
| Microsoft Security Blog RSS | Metadata-only by default | Approved title, publisher/byline, original URL, GUID, publication date/precision, approved categories and retrieval metadata; optional exact excerpt only under an explicit field/length/use permission | Metadata/transient processing rights are unresolved, not presumed exempt. No raw feed archive, full article, automatic article request, default description or content:encoded retention. |
| Google Threat Intelligence/Mandiant RSS | Metadata-only by default | Same allowlisted fields, with configured feed, final transport URL and publisher article URL distinguished; only verified original-link extensions | Same rights gates; FeedBurner access/redirect terms also need checking. No paid portal/API, tracking-link crawl or full feed archive. |

A source policy record must identify a stable policy ID/version, source and exact
endpoints, authority/terms references and review date, permitted transient
processing, retained fields, excerpt selector and maximum length (default off),
allowed uses/sharing, raw-retention mode, retention deadlines per data class,
backup treatment, operator approval and next review/expiry. Unknown permission
means disabled, not an implicit default. Record the policy version on each
processing manifest/observation and evidence's creation provenance. This log is
not a legal determination or redistribution license. The owner must resolve any
uncertain rights basis before B1 verification, including receiving embedded articles.

Full `content:encoded` and even `description` may contain articles. The parser
must not persist these fields simply because the feed calls them a summary.
Default excerpt is absent. An approved excerpt must be an exact bounded selection
from an explicitly allowed decoded source field, with field/selection locator,
permission reference and its own UTF-8 digest. Never summarize, replace with a
title, manufacture placeholder text, or silently truncate an over-limit field.
An over-limit approved field rejects the source batch; ignored fields are still
subject to total response and parsing-work caps. No HTML rendering or URL fetching.

## Representations and V1 compatibility (D011/D019)

V1 SourceItem requires a nonblank excerpt, and EvidenceRecord validates its exact
excerpt hash. Keep those schemas, fixtures, validated copies and existing
Collector/FetchedDocument/EvidenceRepository signatures unchanged. Metadata-only
items must never be coerced into V1 with empty, invented or substituted excerpts.

Propose a separate core `EvidenceRevisionV2` (`schema_version: "2.0"`, distinct
kind), with a discriminated representation. This is a later M1-02a contract PR,
not part of M1-01. Both representations use one common provenance envelope:

| Field group | Proposed semantics |
| --- | --- |
| Identity | Evidence UUID, logical item UUID, source ID, exact source-native ID when supplied; exact original URL fallback with explicit key type when native ID absent |
| Attribution | Publisher, exact title, original article/advisory URL; separately recorded configured/final feed URLs via the retrieval reference; no guessed author or canonical URL |
| Dates | Original publication text when permitted, precision `unknown/date/timestamp`, parsed date or aware timestamp only if supported by the source; parse outcome `missing/valid/invalid`. Invalid/missing remains unknown; retrieval time is separate. CISA dateAdded/dueDate stay labeled catalog fields. |
| Lineage | First-observed 200 retrieval ID/time, source-item locator, adapter version, identity-profile version, parent derivation IDs (not temporal predecessors), creation policy reference and declared schema version |
| Evidence limits | Confidence unknown and TLP null unless supplied; no automatic Ghana relevance, targeting or attribution. Optional permitted excerpt is a separate object with its own hash and permission/selection reference. |
| Integrity | Retained-content SHA-256 over the documented canonical retained field projection; optional response digest reached through the retrieval record. These two digests have different meanings. |
| `raw_snapshot` branch | Required association to a permitted complete response artifact and digest at initial commit; original catalog fields preserved, with entry locator. Current availability is checked separately, never inferred forever from the historical association. |
| `metadata_only` branch | Only the policy's allowlisted retained fields and optional permitted excerpt; no raw artifact ID/path/BLOB, original-body field or catch-all source metadata dictionary. Explicit `raw_retained: false` for this acquisition. |

The raw artifact stores the exact complete entity bytes **after Content-Encoding
decoding but before character/XML/JSON parsing**. Label this digest domain
`decoded-http-entity-v1`; it is not a wire-byte hash. Keep media type, encoding and
byte count. Required SHA-256 verifies a retained artifact. A metadata-only fetch
may compute the same digest in bounded memory and discard bytes; the nullable
response digest then describes an observation, never an archive location. Record
`not_computed` explicitly if absent; never hash a partial failed body as complete.
M1-01 models these descriptors only, without hashing or fetching behavior.

The retained-content digest instead covers versioned canonical UTF-8 JSON of the
**retained item fields**, not the original response. Document the exact projection,
key ordering, decoded-text handling and null/absent rules; no non-finite numbers.
Do not label reconstructed JSON an original publication or exact response.
A local hash detects changes against a known record; it is not a publisher
signature, proof of authenticity, or proof of an article's unretained contents.
Weak ETags are opaque cache validators, not content digests. A 304 computes no
new response digest and does not claim byte equality verified by the collector.

Separate records carry availability/deletion history; immutable evidence is not
silently edited to imply it still has raw backing. A resolver must return the
record kind/version and `available/expired/deleted/unavailable` backing state.
Later repository protocols may return V1 or V2 through an explicit tagged union;
existing V1 EvidenceRepository remains V1. Reports' UUID references alone do not
implement that resolver. No automatic V1 migration or evidence-strength upgrade.

## Identity, observations and processing manifests (D012/D019)

Logical keys are `[source_id, native-key-kind, exact-native-ID-or-original-URL]`.
Including `native-key-kind` prevents a GUID that resembles a fallback URL from
colliding with it. Do not strip meaningful URL queries or merge sources.
Use fixed versioned UUIDv5 namespaces and golden vectors as proposed in the PR
plan. Revision identity includes logical identity, representation/identity profile
and the digest of allowed retained fields, including any permitted excerpt and
publication precision. Exclude retrieval time, item position, cache headers and
administrative policy renewal dates. A change of retention mode/field projection
requires a new profile and revision; a renewal with identical permissions does not.

Repeated unchanged retained content reuses the immutable revision and adds an
observation for each parsed 200. A→B→A reuses still-available A without modifying
its parents. Do not reuse a deleted/tombstoned revision to restore removed fields;
re-acquisition requires explicit policy review and a reviewed identity rule.
Metadata unchanged means **retained metadata unchanged**, not article unchanged.
An unretained description/article change can change the response digest without
changing any item revision; capture the response observation, not invented detail.

A successful source batch commits a processing manifest containing retrieval ID,
source/endpoint/request-variant identity, adapter/schema/profile versions, policy
ID/version, mode, exact observed item-to-revision/retained-digest set (possibly
empty), optional raw artifact reference, and a digest of that canonical manifest.
This supports completeness checks without keeping vendor XML. Observations link
the parsed 200, evidence kind/version/ID, locator and policy. A 304 creates a
retrieval check referencing the manifest's original 200, never per-item observations.

## Conditional requests without raw retention (D019)

A checkpoint is eligible only after a complete 200 batch and its manifest have
committed. Scope it to source, approved configured/final endpoint, fixed request
representation headers and supported Vary fields. Record sent/returned validators
and the stable 200 representation reference. No 304-to-304 chains.

| Prior state | Valid 304 behavior |
| --- | --- |
| Raw-backed, policy current, complete manifest and verified artifact/records available | Record successful check, update returned validators/check time; do not parse, recreate evidence or claim new article verification. |
| Metadata-only, policy current, complete manifest and retained projections/digests available | Same behavior **without any raw snapshot**. Intentional non-retention is valid, not corruption. A stored response hash is optional and is not the checkpoint's proof of completeness. |
| Missing/corrupt required records/manifest (or required raw artifact), changed parser/profile/endpoint/request variant | Invalidate conditional state. If rights remain valid, one unconditional fetch may use the remaining attempt budget; otherwise defer. No reconstruction of missing items from a hash. |
| Expired/revoked rights, deletion required, or unsupported policy transition | Pause; do not extend retention, restore deleted records or automatically re-fetch. Permission renewal is a separate decision. |
| Unsolicited 304, changed redirect target, mismatched source/variant or incompatible validators | Protocol failure; no successful checkpoint. Validate each redirect and do not forward old conditionals to an unapproved/different representation. |

Unexpected Vary fields (including `*`) disable conditional reuse. Unsupported
Cache-Control directives that prohibit storage cause a fail-closed policy review;
HTTP caching directives are not a copyright license. A 304 cannot replay newly
approved parser fields: without original bytes a separately authorized full 200
is required. It cannot renew a rights deadline or prove the original article URL
is unchanged/reachable. Tests must cover both valid metadata-only 304 and invalid
raw-backed 304 with a missing required artifact.

## SQLite, transient data and retention (D013/D017/D020)

Propose one private SQLite store: versioned evidence/retained projections,
retrieval descriptors, manifests, observations, source checkpoints, policy
references, safe failure events and availability/tombstones. Optional
content-addressed BLOB artifacts are **only for approved raw-backed sources**.
A metadata-only write API accepts typed allowlisted projections and descriptors,
never a raw byte parameter. Reject mixed-mode artifacts/unknown fields and
policy-mode mismatches; adapter flags alone are not authorization.

Validate the entire source batch, then atomically commit its permitted contents,
manifest and checkpoint; no network I/O in the transaction. Foreign keys,
operation idempotency, conflict rejection, one-writer/run, crash/disk-full rollback,
schema compatibility and consistent SQLite backups remain required. A separate
safe failure event never advances the successful checkpoint. Artifact ownership
and deletion are policy-scoped; shared hashes must not accidentally extend one
source's retention or grant another source access.

Vendor response bytes exist only in bounded transport/parser memory, including
failure paths. No HTTP disk cache, temporary body spool, raw exception/object
repr, database payload column, WAL entry, debug dump, tracing attachment, LLM
request, test recording, CI artifact or public fixture may contain them. Drop
references promptly after projection/failure; Python does not guarantee secure
memory erasure. Before live use, approve a host with core/crash dumps disabled,
no unencrypted swap/hibernation, and backups that exclude process memory and
temporary buffers. Prefer no swap for the collection process. Encryption alone
does not authorize retention. Verify a synthetic distinctive forbidden marker is
absent from DB/WAL, backups, logs, failure diagnostics and artifacts. Such tests
do not prove host-level memory protection; the operator must verify it separately.

No blanket vendor 365-day promise. Set source-specific maximum deadlines for
metadata, excerpts, digests, retrieval/HTTP fields and audit records before B2;
304s and repeated observations do not silently reset them. For permitted CISA
raw snapshots/records, retain the proposed 365-day reporting target only within
approved policy/capacity; unreferenced permitted artifacts may use a 30-day cap.
Vendor raw storage has zero durable retention; transient-processing permission
still needs review. Seven encrypted daily backups are a proposal, not a right
to keep expired data seven extra days.

Deletion must inventory live rows, indexes, SQLite free pages/journals/WAL,
replicas/exports and every backup. Before activation, approve/test a practical
purge/compaction and backup expiry procedure with an operator and deadlines;
SQLite DELETE alone is not verified erasure. Purge/replace or retire every
containing backup by the source deadline, even when that reduces restore points.
If that cannot be enforced, do not onboard the source. Restore in isolation and
apply the current policy/deletion ledger before any access or checkpoint reuse.
Tombstones retain only fields/digests independently permitted after deletion;
otherwise keep a minimal permitted opaque audit event, not a permanent hash by
assumption. Expiry/deletion invalidates affected conditional checkpoints and marks
citations unavailable. Do not silently remove cited evidence for disk space or
retain it against permissions; pause and obtain review of the resulting evidence gap.

## Reporting compatibility and evidence gaps (D018/D021)

The existing report-template choice remains authoritative and is not modified.
[REPORTING_STANDARDS.md](../REPORTING_STANDARDS.md) points to the external CTI
report template and explicitly says its contents are not reproduced in this
repository. No template artifact exists in this checkout. This is therefore an
assessment against the checked-in reporting requirements, **not** a verified
field-by-field review of that external template. Obtain the authoritative version
and review its license before later report tooling; no substitute is proposed.
The Microsoft reference is for analytical depth, clarity and evidence quality,
not a new reporting standard. No template, reporting code or publication changes.

| Existing reporting requirement | Hybrid support and limitation / human action |
| --- | --- |
| Verifiable facts and evidence dates | CISA retained entries can be re-read and rehashed with catalog context. Vendor metadata supports facts about the feed listing only; an absent body/digest alone cannot substantiate article-level claims. |
| Citations | Preserve publisher, original URL, supplied title/date precision, retrieval/check times, evidence ID and retention mode. Label link-only/unavailable backing; feed retrieval is not an article-access timestamp. |
| Technical findings, IOCs and TTPs | KEV fields support catalog facts, not exploitation telemetry. Metadata-only titles are discovery leads. Analysts need permitted exact supporting evidence or corroboration before technical assertions; no blind indicator extraction/blocklists. |
| Confidence, uncertainty and Ghana relevance | Keep unknown defaults. Analyst distinguishes source claims, corroborated facts, hypotheses and gaps; global coverage does not establish Ghana targeting. Local exposure/targeting needs evidence and rationale. |
| Conclusions and defensive actions | Human judgment must explain evidence, applicability and uncertainty. Catalog requiredAction/dueDate are source fields, not automatically Ghanaian mandates. Vendor headlines cannot supply detailed recommendations alone. |
| Review, TLP and publication | Maintain private handling and original markings. Resolve D009 inheritance, authenticated reviewers and exact-revision approval before any exporter. D018 keeps the existing template and human control; no automatic publication. |

For a later human-led investigation, an analyst may independently open the cited
original publication under applicable access terms, record actual access time,
claim/section locator, source version and verification outcome, and link permitted
supporting excerpts or independently corroborating material. This is a proposed
later verification workflow, not an automated article fetch or implemented UI.
Any lawfully retained new evidence is a new linked acquisition, never a retroactive
claim that M1 archived the page. If a page changes/disappears and no permitted copy
exists, the historical claim cannot be independently reproduced from a hash.
Mark that gap, find independent corroboration, narrow the claim, or omit it.
Analyst attestation alone does not recover missing material. Evidence sufficiency,
claim-level linkage and authoritative template/license review remain open before
report tooling; the M1 records are a foundation, not finished intelligence.
