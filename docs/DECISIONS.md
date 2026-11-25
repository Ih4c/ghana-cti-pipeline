# Decision log

Keep IDs stable. Record date, status, rationale, consequences, and a durable
approval reference. Use accepted, proposed, open, rejected or superseded; never
mark a proposal accepted merely because its documentation merged. Record future
approval against the specific milestone version and any conditions.

| ID | Date / state | Decision or proposal | Basis and consequences |
| --- | --- | --- | --- |
| D001 | 2026-11-18, accepted baseline | Modular single Python distribution; shared typed contracts, independent adapters/storage; open-source tooling and fixture CI | Delivered by [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2) and [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3). Deployment/storage remain unselected. |
| D002 | 2026-11-18, accepted permanent requirement | Ghana-focused evidence discipline; AI partly in Stage 1 and optionally in Stage 2; Stages 3–5 human-led; explicit approval and TLP:CLEAR for public output | Existing [workflow](CTI_WORKFLOW.md), [requirements](REQUIREMENTS.md), [reporting standards](REPORTING_STANDARDS.md) and AGENTS. No autonomous attribution or publication. |
| D003 | 2026-11-18, accepted permanent requirement | All commit author/committer names are `ih4c`, with the noreply address in AGENTS; no personal identities or prohibited trailers in metadata/text | Explicit owner instruction, preserved in [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3) and [AGENTS.md](../AGENTS.md). Verify every commit before push. |
| D004 | 2026-11-19, proposed onboarding; v1.3 revision | CISA complete permitted catalog; Microsoft RSS content:encoded and Google RSS description full articles | D022 strategy accepted. Vendor mappings are owner observations from 2026-11-18, not independently reconfirmed. Rights/B1/B2 remain open; no metadata fallback or article crawler. |
| D005 | 2026-11-23, accepted for offline M1-03 only | Private SQLite evidence, retrieval/observation/manifests and permitted original/derived BLOB artifacts for all three sources | Revises metadata-only vendor target. D013/D019/D024 keep response versus item/transform content distinct; offline backend scope approved below; real-content retention/hosting remains gated. |
| D006 | 2026-11-19, proposed | Manual CLI first; separately approved daily timer with one automatic cycle per source/24 hours | Persist attempt/cycle budgets across retries/recovery/restarts; stricter publisher limits override. B1/B2/C separate. No schedule enabled. |
| D007 | 2026-11-24, offline M1-04 accounting approved; cap unchanged | Zero incremental paid-service budget and 2 GiB live-store cap, with WAL/headroom and encrypted backup accounting | Full-text response/artifact budget up to 64 MiB/day before overhead; fewer than 32 such days fit. Measure pilot and obtain explicit capacity/retention decision; no silent expansion or purchase. |
| D008 | 2026-11-24, offline M1-05 transport and M1-06a XML parsing approved; other controls gated | Preserve SSRF/TLS/proxy/request/XML/isolation controls; add full-text transformation and private artifact protection | D024 offline HTML/plain-text helpers are separately approved; D032 records the concrete profile for review. Real bodies may enter only an authorized private evidence store, never public Git/PR/CI/logs; this revises transient-only vendor storage assumptions. |
| D009 | 2026-11-18, open; required before exporter | Derived intelligence must not be less restrictive than its sources; resolve evidence, unknown markings and intersecting recipient restrictions | F4 strict xfail records intended CLEAR/RED rejection. Need FIRST guidance review and authenticated review/access design; not numeric TLP ordering alone. M1 has no exporter. |
| D010 | 2026-11-18, accepted coordination baseline | Permanent requirements in AGENTS/core docs; milestone versions, status/decision ledger and reusable handoff; first-task file historical | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4) merged at `50224b3`; owner explicitly designated its documentation the coordination baseline. This is not acceptance of M1 technical proposals or implementation. |
| D011 | 2026-11-19, accepted for M1-01 only | Additive 200/304/failure descriptors and observations; no receipt-to-retention inference | Owner approval verified in the linked record below; M1-01 only under v1.3. Existing V1/protocols unchanged; descriptor-only scope excludes V2, hashing, I/O and later increments. |
| D012 | 2026-11-23, accepted for M1-02b pure helpers; storage semantics proposed | Immutable source revisions include original selected article content; transformations have separate versioned derivation identities | Original changes matter even if sanitized output is unchanged. Reuse available A in A→B→A via chronological observations, never edit parent/history or resurrect revoked/deleted content. |
| D013 | 2026-11-23, accepted for offline M1-03 only | Atomic SQLite response/original/derived/evidence/manifest/checkpoint BLOB transactions | BLOBs simplify recovery but amplify storage/WAL/backups. Separate artifacts deferred pending measured need and explicit design. Required derivation failure rolls back whole source batch. |
| D014 | 2026-11-24, offline M1-05 mechanisms approved | Direct-only validated-IP connections with original-host TLS; manual validated redirects; no inherited/explicit proxies | Prove DNS-to-socket binding and revalidation at every hop/retry. Standard-library transport with injected primitives; no live I/O or default resolver. Use approved direct egress, never bypass environment restrictions. |
| D015 | 2026-11-24, offline M1-05 transport and M1-06a parsing approved; operations gated | Whole-source batches; three attempts/180-second source and 10-minute run budgets; existing UTF-8/depth/header/byte/item limits | Recovery and transforms share budgets; 403 pauses, 429 honors Retry-After; source errors isolated. D024/D032 bind full-text/node/attribute/aggregate bounds for offline M1-06b, never silent truncation. |
| D016 | 2026-11-19, proposed; boundaries preserved | Gate A names offline implementation increments; B1 authorizes bounded verification; B2 manual collection; C recurrence | Gate A approved for M1-01 only via the owner comment below; M1-02a is separately approved below; M1-02b pure helpers are separately approved below; M1-03 offline persistence is separately approved below; M1-04 offline recovery/lifecycle is separately approved below; M1-05 offline transport is separately approved below; M1-06a pure parsing is separately approved below; M1-06b offline HTML/text helpers are separately approved below; M1-07 onward and B1/B2/C remain unapproved. |
| D017 | 2026-11-24, offline M1-04 mechanisms approved; lawful basis unresolved | Source-specific lawful basis and deadlines for complete feed/item originals, derivatives, metadata/digests and backups | D023 risk acceptance is not rights clearance. Prohibited/unresolved full-text mode blocked; written permission, applicable grants or other legally supported grounds require scope review. No metadata substitution. |
| D018 | 2026-11-19, superseded collection strategy by D022 | Historical v1.2 metadata-first vendor target; no longer the intended final capability | Original accepted decision remains in PR #6/Git history. Report-template authority, quality-reference-only Microsoft role and human control are preserved and reaffirmed in D022. |
| D019 | 2026-11-23, contracts and offline M1-03 persistence accepted; operations proposed | Additive V2 catalog_entry/feed_full_text modes, response/item/derived digests, availability and full-text manifests | Eligible 304 now requires intact permitted original/derived backing; v1.2 metadata-only exception no longer targets collection. V1/M1-01 unchanged; M1-02a V2/data contracts delivered by PR #9 under the approval below. M1-03 offline backing/checkpoint scope approved below; live operations remain gated. |
| D020 | 2026-11-24, offline M1-04 mechanisms approved; real-host controls pending | Authorized full-text in encrypted private storage with policy-scoped deletion of originals/derivatives/WAL/backups; no public/log leakage | Host dump/temp/swap controls and consistent isolated restore required. SQL DELETE is not verified erasure; rights expiry invalidates checkpoints. M1-04 offline mechanisms approved below; no real content fixtures or operational jobs. |
| D021 | 2026-11-19, open; before report tooling | Template artifact/version/license, claim-level evidence sufficiency and publication permissions | Retained source text improves reproducibility, not truth or automatic Ghana attribution. Existing template unchanged; no full articles/extensive excerpts in output. D009 review/TLP gates remain open. |
| D022 | 2026-11-19, accepted strategy only | Full-text collection from all three selected sources where authorized: complete CISA fields, Microsoft RSS content:encoded and Google RSS description; metadata-only vendor collection rejected as final target | Explicit owner task “M1 v1.3 Full-Text Collection Decision,” recorded here without a session link. Supersedes D018 collection direction and affected target assumptions in D004/D005/D008/D012/D013/D017/D019/D020. Existing report template and human workflow remain authoritative. No implementation/source-access approval. |
| D023 | 2026-11-19, accepted owner risk acknowledgement; rights clearance open | Owner reports Microsoft copying/distribution/publication and permitted-use restrictions, calls for applicable Google terms/robots review, and accepts identified operational/legal risk for private research | Owner-reported findings are not independently verified legal conclusions. Risk acceptance is not a license/exception or authority to disregard restrictions. [Open rights questions/routes](milestones/M1_EVIDENCE.md) require established lawful basis before activation. Commercial use/republication needs separate review and necessary written authorization. |
| D024 | 2026-11-25, offline M1-06b HTML/text implementation approved; operational use gated | Separate original feed HTML, sanitized HTML and plain text with independent hashes, parent links and transformation versions; explicit HTML/node/attribute/derived-byte caps | [Evidence design](milestones/M1_EVIDENCE.md) specifies inert allowlist, safe encoding/entities, no execution/resource loads, immutable transformations and bounded processing. CISA remains structured catalog content. M1-06b standard-library helpers have separate scoped approval below; D032 records exact policy/bounds for review. Source feasibility, viewer safety and operational use remain gated. |
| D025 | 2026-11-19, proposed wire bindings; delivered within M1-02a (PR #9) | Freeze the data-only contract serialization, domain labels, helper versions and explicit supplementary bounds in [contract reference](M1_EVIDENCE_CONTRACTS.md) | Prose requirements lacked exact field/domain spellings and some list bounds. M1-02b supplies separately approved canonicalization/ID/hash helpers; no runtime rights claim. Existing wire shapes and domain labels stay unchanged. |
| D026 | 2026-11-23, resolved and delivered by PR #16 | Separate stable source revisions, versioned derivations and immutable artifact/evidence/manifest associations | [Frozen projections and namespaces](M1_IDENTITY_PROFILES.md) define source-only evidence_id, separate derived IDs, and an evidence-association key over canonical metadata. Parsed metadata and transforms cannot change an unchanged source revision. Existing wire shapes remain intact; M1-03 must use association keys rather than overwrite by evidence_id. Scope approved in the PR #15 owner comment below. |
| D027 | 2026-11-19, accepted numeric-cap amendment; Issue #10 open | RSS transferred and decoded response caps each 6 MiB; original HTML, sanitized HTML and plain-text batch aggregates each 6 MiB; per-article fields remain 1 MiB | [Owner decision](https://github.com/Ih4c/ghana-cti-pipeline/issues/10#issuecomment-7008185129) approves numeric validation changes, synthetic boundary tests and documentation under v1.3 without schema redesign. B1 measurements remain planned to confirm headroom and do not block this change. No live requests, activation or B1/B2/C approval; [capacity analysis](milestones/M1_RSS_SIZE_INVESTIGATION.md) rises to 64 MiB/day before overhead, with unchanged 2 GiB live-store and 512 MiB/day transfer caps. |
| D028 | 2026-11-24, implementation binding delivered by PR #17 | SQLite schema v1, immutable association edges, policy selectors and complete backing checks | [Storage reference](M1_SQLITE_STORAGE.md): application ID 0x47435449, rollback journal/FULL synchronization, explicit write transactions/read snapshots, no migrations, exact replay without checkpoint rewind. Additive V2 store leaves the V1 repository protocol/backend target unchanged. These concrete choices implement the approved scope; they do not grant production, backup/purge, rights or activation approval. |
| D029 | 2026-11-24, implementation binding delivered by PR #18 | POSIX private workspace, independent rights ledger, conservative capacity reservations, consistent backups, isolated restore and whole-policy purge | [Lifecycle design/runbook](M1_LIFECYCLE.md). Keep M1-03 schema v1; ledger has its own schema v1 and independent time-bounded authority. Count all managed copies within 2 GiB. Restore strips operational selectors. Purge retires all managed backups/restores, compacts live storage and records completion only afterward. Tested logical absence is not physical erasure, host encryption or rights clearance. |
| D030 | 2026-11-24, implementation binding delivered by PR #19 | Standard-library transport with exact URL profiles, all-answer IP validation, pinned numeric sockets/TLS, bounded HTTP framing/decoding and caller-owned budgets | [Transport reference](M1_TRANSPORT.md). No production resolver/socket defaults or endpoints. Narrow ASCII HTTP/URL and identity/gzip/deflate profiles; 32 KiB response headers, independent wire/decoded caps, safe outcomes and separate transient body bytes. Transfer counters distinguish coded entity from framing and caller-reserved overhead. Real-host/source verification remains separate. |
| D031 | 2026-11-25, implementation binding delivered by PR #20 | Pure Expat RSS 2.0 and JSON envelope parsing, exact selected fields, bounded complete batches and no source-specific mappings | [Parsing reference](M1_PARSING.md) specifies channel validation, expanded field names, duplicate semantics, transient results and safe errors. Finite JSON decimals are preserved exactly; the integer-only canonical profile remains unchanged and rejects incompatible values. A 4,300-digit integer safety ceiling is explicit. Syntax validates complete fields, not publisher article completeness. |
| D032 | 2026-11-25, concrete implementation binding proposed for independent M1-06b review | Separate versioned standard-library sanitizer/extractor, strict balanced fragments, attribute-free inert output and independent original/derived batch limits | [Transformation reference](M1_TRANSFORMS.md) fixes the allowlist, removed subtrees, canonical escaping, text separators, node/attribute accounting and Python 3.11/3.14 lexical modes. No browser-style repair, new dependency, storage integration or original replacement. Outputs do not establish rights, viewer safety or source completeness. |

## Verified M1-06b authorization — 2026-11-25

The [owner comment on PR #20](https://github.com/Ih4c/ghana-cti-pipeline/pull/20#issuecomment-7149971631),
authored by repository owner `Ih4c`, explicitly approves M1-06b under v1.3 / D024
as a pure offline increment. Author/scope were verified before application changes.
PR #20 is merged at `64224f1`, the verified main baseline for this increment.

Approval covers deterministic HTML sanitization and plain-text extraction of
already-extracted article strings with Python standard-library `html.parser`;
separate sanitizer/extractor versions; inert outputs with no active elements,
attributes or external-resource references; no link following; 1 MiB fields,
6 MiB representation aggregates and depth 64; finite errors without payloads or
partial output; unchanged originals, synthetic adversarial tests and documentation.
The subsequent owner task clarification permitted evaluating other parsers for
security, otherwise retaining the comment's approach. This implementation stays
standard-library-only; no dependency change was made.

D032 records the exact narrow grammar, allowlist, serialization, reference decoding,
text separators and D024 node/attribute budgets for independent review. Earlier
contracts, protocols, schemas, digest/identity profiles and report template remain
unchanged. Helpers do not access network, filesystem, clock, randomness, transport
or storage and do not create evidence associations or analytical claims.

No adapters (M1-07–09), storage integration, CLI/orchestration, live requests,
B1/B2/C, scheduling, deployment, publication, full-text activation or paid services.
Lawful basis stays open and blocks real full-text activation; Issue #10 stays open.
Existing 2 GiB and $0 caps remain. Stop at the dedicated PR for independent review;
do not merge. The next proposed increment, M1-07, requires separate approval.

## Verified M1-06a authorization — 2026-11-24

The [owner comment on PR #19](https://github.com/Ih4c/ghana-cti-pipeline/pull/19#issuecomment-7138988824),
authored by repository owner `Ih4c`, explicitly approves M1-06a under v1.3,
limited to D015 and the safe-parsing portion of D024. Author/scope were verified
before application changes. PR #19 is merged at `170ab1a`, the verified main
baseline for this increment.

Approval covers pure offline RSS 2.0 XML and JSON catalog parsing with synthetic
fixtures: UTF-8/optional BOM, conflicting encoding rejection, no DTD/custom
entities/external resources, duplicate JSON key rejection, depth 64 and finite
numbers; complete supplied item/entry fields; 6 MiB RSS/8 MiB catalog input,
500/10,000 items, 1 MiB article fields and existing metadata limits. Reject invalid
or empty envelopes, conflicting native IDs and missing/empty/structurally truncated
bodies as whole batches without metadata fallback. Empty valid RSS is valid, not
a retraction. Original response bytes remain separate from XML-decoded field values.
Use only the standard library, specifically Expat for XML; no dependencies added.

D031 records concrete choices for independent review, not separate production or
source approval. The parsers do no I/O, storage/transport imports, clock reads or
randomness. All M1-01–05 models/interfaces/profiles stay unchanged; no schema
migration, altered digest domain, report change or new source mapping. Existing
D027, 1 MiB article, 8 MiB generic, 2 GiB storage and $0 paid-service caps remain.

No HTML parsing/sanitization/text extraction (M1-06b), adapters/source mappings
(M1-07–09), storage integration, live requests or linked-page fetching, real feed
content, deployment, scheduling, publication or paid services. Issue #10 stays
open for future B1 measurement. That comment did not approve M1-06b; the separate
PR #20 approval above now covers it. B1/B2/C remain unapproved. M1-06a was delivered
by PR #20 after its independent implementation review.

## Verified M1-05 authorization — 2026-11-24

The [owner comment on PR #18](https://github.com/Ih4c/ghana-cti-pipeline/pull/18#issuecomment-7119629449),
authored by repository owner `Ih4c`, explicitly approves M1-05 under v1.3, limited
to D008/D014/D015 offline hardened HTTPS transport producing existing M1-01
retrieval descriptors. Author/scope were verified before application changes.
PR #18 is merged at `e4d6a0a`; the new feature branch starts from verified main.

Approval includes exact approved HTTPS host/path and port checks; all-address
DNS validation, numeric-IP connection and original-host SNI/certificate checks;
redirect/retry revalidation, no proxies, 32 KiB headers, independent 6 MiB RSS/
8 MiB KEV wire/decoded caps, bounded decompression, 5/20/60/180-second timeouts,
project-contact User-Agent, conditionals, transient/429/5xx retries, backoff/jitter,
Retry-After deferral, 403 pause, caller-supplied budgets and safe M1-01 outcomes.
Only standard-library mechanisms and existing core contracts are used; no new
dependency. D030 records exact profiles and accounting choices for independent
review, not as separate source or production approval.

Tests inject resolver/socket/TLS/clock behavior and block real DNS and socket
connections. Preserve all earlier contracts, protocols, D027 6 MiB RSS, 1 MiB
article, 8 MiB generic, 2 GiB storage, 512 MiB/day transfer and $0 paid-service
bounds. HTTP byte grants cannot account for unobserved DNS/TLS/IP overhead; the
caller must reserve that separately before granting bytes. Persisted/global/day
budget enforcement is excluded, not silently implemented or claimed.

No live source requests or DNS, source registry/default endpoints, robots or
policy fetching, source parsing, sanitization, adapters, storage integration,
persisted retry budgets, scheduling, deployment, publication or paid services.
Issue #10 stays open for separately approved B1 measurements. B1/B2/C and later
increments were not approved by that comment. M1-05 was delivered by PR #19;
the separate PR #19 approval above now covers M1-06a only.

## Verified M1-04 authorization — 2026-11-24

The [owner comment on PR #17](https://github.com/Ih4c/ghana-cti-pipeline/pull/17#issuecomment-7119143529),
authored by repository owner `Ih4c`, explicitly approves M1-04 under v1.3: D017 and
D020 as offline mechanisms, D007 capacity accounting and recovery/lifecycle for
the merged M1-03 store. Author and scope were verified before application changes.
PR #17 is merged at `c256b3f`; the new branch starts at that verified current main.

Approval includes crash/FULL/read-only/schema/locking handling, 2 GiB accounting
with 80% warning and journal/WAL/temporary write headroom, consistent SQLite
backup, isolated verified restore, expiry/revocation/purge of original/derived
copies and associations/checkpoints, an append-only rights/deletion ledger,
focused tests, synthetic fixtures, a runbook and related documentation. D029
records concrete choices for independent review, rather than assuming the scope
approval endorses every implementation detail.

Existing core contracts, helper semantics, M1-03 behavior/schema, D027 6 MiB RSS,
1 MiB per-article, 8 MiB generic, 2 GiB storage and $0 paid-service bounds stay
unchanged. Issue #10 remains open for separate B1 measurement. Use only synthetic
data and temporary databases. SQL DELETE is not verified erasure; the implementation
checks compaction and managed journal/WAL/backup handling and explicitly limits its
claim to logical managed-file absence, with independently permitted shared content
remaining available through its surviving associations.

Production paths, real content, network access, parsing, sanitization, adapters,
operational backup/purge jobs, key management, deployment, scheduling, publication
and paid services remain excluded. This approval establishes no lawful full-text
retention basis under D017/D023. Real-host validation remains required before B2;
B1/B2/C and later increments need separate approval. Stop at the dedicated PR for
independent review.

## Verified M1-03 authorization — 2026-11-23

The [owner comment on PR #16](https://github.com/Ih4c/ghana-cti-pipeline/pull/16#issuecomment-7108040658),
authored by repository owner `Ih4c`, explicitly approves M1-03 under v1.3, limited
to D005/D013/D019 offline SQLite persistence for approved M1-01/M1-02a/M1-02b.
Author and scope were verified before application changes. PR #16 is merged;
its main merge is `8a3a85d` (reverified 2026-11-24).

The approved scope is atomic response/item/derived-representation/manifest/
retrieval-observation/checkpoint storage, policy-bound BLOB associations,
immutable keys rejecting conflicts, FK/reference integrity, replay idempotence,
rollback, and all required backing for valid 304s. Focused synthetic tests,
temporary databases and related documentation are included. Existing contracts,
helpers, D027 6 MiB RSS, 1 MiB per-article and 8 MiB generic limits stay unchanged.
Issue #10 stays open for separate B1 measurement.

D028 records the exact schema/API binding for review, without treating the scope
approval as approval of every implementation choice. Source revisions group
immutable full-bundle association keys; content-addressed bytes are reached only
through policy-bound artifacts. Read eligibility checks hashes, availability,
retention and the original 200/manifest/observation chain. Historical metadata
reads are internal and do not assert retained-body availability or publication rights.
The additive V2 API does not implement the legacy V1 repository protocol; the
whole-M1 V1-backend target remains deferred, with its signature unchanged.

This approval excludes production paths, real source content, network access,
parsing, sanitization, adapters, backup/purge jobs, deployment, scheduling,
publication and paid services. That comment did not cover M1-04. The separate PR #17 approval above now covers
offline recovery/lifecycle only; B1/B2/C remain unapproved. No operational source or job is enabled. Stop at the dedicated
implementation PR for independent review.

## Verified M1-02b authorization and D026 resolution — 2026-11-23

[Owner approval on PR #15](https://github.com/Ih4c/ghana-cti-pipeline/pull/15#issuecomment-7008787831),
authored by repository owner `Ih4c` on 2026-11-19, was verified before application
changes and rechecked on 2026-11-23. It approves M1-02b under v1.3: D012/D024 identity/digest helpers, D026 resolution,
canonicalization profiles, deterministic UUIDv5 IDs, SHA-256 computation, synthetic
vectors, focused tests and documentation. It reaffirms source revision independence
from sanitizer/extractor versions, immutable parent associations, existing contract
compatibility, D027's 6 MiB limits and keeping Issue #10 open. The earlier
[PR #9 approval](https://github.com/Ih4c/ghana-cti-pipeline/pull/9#issuecomment-6997682376)
is consistent; the later PR #15 comment is the current scope reference.

Before implementation, [M1_IDENTITY_PROFILES.md](M1_IDENTITY_PROFILES.md) records
exact projections, domain/hash pairs, fixed namespaces and canonical JSON rules.
D026 is resolved without changing approved wire fields: evidence_id groups the
source revision, while a computed evidence-association UUID identifies the entire
immutable bundle. A manifest's evidence ID plus metadata digest identifies that
association; derived representations have separate parent/version-bound IDs.
Catalog revisions use complete original entry digests; feed revisions add only
explicit supplied source metadata to the original field digest. Parsed date/field
interpretations are excluded from source revision identity, but remain hashed in
association metadata. A → B → A reuses A's revision while retaining distinct
acquisitions, observations and processing associations.

This approval does not cover persistence, network/DNS access, parsing, sanitization,
adapters, scheduling, deployment, publication or paid services. That approval did not cover M1-03; the later PR #16 comment above
now covers offline persistence only. B1/B2/C remain unapproved. No contract/schema migration or report-template change.

## Verified D027 authorization — 2026-11-19

The [owner comment on Issue #10](https://github.com/Ih4c/ghana-cti-pipeline/issues/10#issuecomment-7008185129),
authored by repository owner `Ih4c`, was verified before application changes. It
explicitly approves raising RSS response caps (transferred and decoded) and each
of the three batch representation caps from 2 MiB to **6 MiB**, with synthetic
exact-limit/one-byte-over tests, updated documentation and capacity calculations.
The **1 MiB per-article** and **8 MiB generic receipt/response** caps stay unchanged;
no schema redesign is intended. Oversized feeds still fail as whole batches,
without truncation or partial parsing. Existing V1/M1-01/protocol signatures and
serialized shapes/versions are preserved; only the accepted RSS numeric range widens.

This owner decision supersedes the earlier D027 proposal to wait for measurements
before changing caps. The selected 6 MiB value is an owner-approved bound, **not a
measured feed maximum or proven headroom**. B1 measurement stays planned and Issue
#10 stays open until it is recorded. No transport/parser/harness implementation,
live requests, source activation, persistence, scheduling, spending or publication
is authorized. B1/B2/C remain separately gated.

## Historical Issue #10 investigation scope — 2026-11-19

The initial owner task “Investigate Issue #10” authorized documentation investigation and
a documentation-only PR, including correction of stale PR #13/Issue #11 status.
At that time no separate authorization for new test code or live B1 measurements was supplied;
the [synthetic regression cases and B1 procedure](milestones/M1_RSS_SIZE_INVESTIGATION.md)
were proposals only. PR #14 delivered that documentation-only investigation. The
subsequent D027 approval above authorizes numeric-cap implementation and synthetic
contract tests, but not live measurement or a measurement harness.
That initial scope changed no numeric limits. The subsequent verified D027
comment approves only the numeric exception and synthetic tests described above.
Issue #10 remains open; PR #12 and PR #13 are merged and Issue #11 is closed.
D022's full-text direction, D026's separate identity work, schema versions,
rights requirements and B1/B2/C gates are preserved.

## Verified M1-01 authorization — 2026-11-19

[Owner approval on PR #7](https://github.com/Ih4c/ghana-cti-pipeline/pull/7#issuecomment-6996754396),
authored by repository owner `Ih4c` on 2026-11-19, explicitly states:

> As project owner, I explicitly approve implementation of M1-01 under M1 v1.3,
> limited to D011 and the retrieval/observation descriptor portion of D019.
>
> This authorization covers additive offline core contracts, synthetic fixtures,
> focused tests and related documentation only.
>
> It does not authorize EvidenceRevisionV2, persistence, transport, parsers, live
> source access, scheduling, deployment or publication.
>
> Create a separate implementation PR for independent review. Do not merge automatically.

This historical comment was verified before M1-01 application edits. It superseded M1-01's prior
pending state, not any other decision. The implementation targets M1_COLLECTION
v1.3 / M1_READINESS review v1.2 without changing their technical scope.

At that time, D011 and only D019's descriptor portion were accepted. Existing
V1/protocols and full-text strategy remained unchanged. D004–D008, D012–D017,
the remaining D019 and D020/D024 stayed proposed; D009/D021 stayed open. No payload hashing behavior, new
dependencies, V2 evidence, source adapters, storage, networking, parsing,
sanitization, operations, paid services or publication are part of this approval.
At that approval, M1-02a onward remained unapproved. The separate M1-02a approval
below supersedes that status only; B1/B2/C remain unapproved.

See [STATUS.md](STATUS.md) for delivery state and
[M1 contract reference](M1_RETRIEVAL_CONTRACTS.md) for implemented behavior/limits.

## Verified M1-02a authorization — 2026-11-19

[Owner approval on PR #8](https://github.com/Ih4c/ghana-cti-pipeline/pull/8#issuecomment-6997113844),
authored by repository owner `Ih4c`, was verified before application edits:

> I approve M1-02a under M1 v1.3, covering D019/D024 data-only evidence,
> artifact-reference, provenance, source-policy and processing-manifest contracts,
> synthetic tests and documentation. All stated implementation exclusions remain
> in force.

PR #8 merged at `9e30ab5a3d88352f97fd7fa64ea2a676097e0e72`; its merged tree matches
the final reviewed implementation branch. Its discussion had no review findings
requiring changes; the approval above is separate from the merge.

This accepts only the D019/D024 contract scope. [M1-02a contract reference](M1_EVIDENCE_CONTRACTS.md)
documents implemented validation and the D025 wire choices/D026 identity gap for
review. No SQLite, HTTP/source access, RSS/JSON processing, HTML sanitization/text
extraction, actual hashing, UUIDv5/identity generation, adapters, scheduling,
deployment, publication or report-template changes. No operational gate is approved.
That historical approval did not cover M1-02b; the separate PR #15 authorization
and D026 resolution above now cover its pure helpers only.
