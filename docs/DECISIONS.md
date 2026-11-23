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
| D005 | 2026-11-19, proposed; full-text revision | Private SQLite evidence, retrieval/observation/manifests and permitted original/derived BLOB artifacts for all three sources | Revises metadata-only vendor target. D013/D019/D024 keep response versus item/transform content distinct; no backend or permission to retain is implied. |
| D006 | 2026-11-19, proposed | Manual CLI first; separately approved daily timer with one automatic cycle per source/24 hours | Persist attempt/cycle budgets across retries/recovery/restarts; stricter publisher limits override. B1/B2/C separate. No schedule enabled. |
| D007 | 2026-11-19, proposed; cap unchanged | Zero incremental paid-service budget and 2 GiB live-store cap, with WAL/headroom and encrypted backup accounting | Full-text response/artifact budget up to 64 MiB/day before overhead; fewer than 32 such days fit. Measure pilot and obtain explicit capacity/retention decision; no silent expansion or purchase. |
| D008 | 2026-11-19, proposed; required before collection | Preserve SSRF/TLS/proxy/request/XML/isolation controls; add full-text transformation and private artifact protection | D024 safe HTML/plain-text design is unimplemented. Real bodies may enter only an authorized private evidence store, never public Git/PR/CI/logs; this revises transient-only vendor storage assumptions. |
| D009 | 2026-11-18, open; required before exporter | Derived intelligence must not be less restrictive than its sources; resolve evidence, unknown markings and intersecting recipient restrictions | F4 strict xfail records intended CLEAR/RED rejection. Need FIRST guidance review and authenticated review/access design; not numeric TLP ordering alone. M1 has no exporter. |
| D010 | 2026-11-18, accepted coordination baseline | Permanent requirements in AGENTS/core docs; milestone versions, status/decision ledger and reusable handoff; first-task file historical | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4) merged at `50224b3`; owner explicitly designated its documentation the coordination baseline. This is not acceptance of M1 technical proposals or implementation. |
| D011 | 2026-11-19, accepted for M1-01 only | Additive 200/304/failure descriptors and observations; no receipt-to-retention inference | Owner approval verified in the linked record below; M1-01 only under v1.3. Existing V1/protocols unchanged; descriptor-only scope excludes V2, hashing, I/O and later increments. |
| D012 | 2026-11-23, accepted for M1-02b pure helpers; storage semantics proposed | Immutable source revisions include original selected article content; transformations have separate versioned derivation identities | Original changes matter even if sanitized output is unchanged. Reuse available A in A→B→A via chronological observations, never edit parent/history or resurrect revoked/deleted content. |
| D013 | 2026-11-19, proposed; full-text revision | Atomic SQLite response/original/derived/evidence/manifest/checkpoint BLOB transactions | BLOBs simplify recovery but amplify storage/WAL/backups. Separate artifacts deferred pending measured need and explicit design. Required derivation failure rolls back whole source batch. |
| D014 | 2026-11-18, proposed; unchanged | Direct-only validated-IP connections with original-host TLS; manual validated redirects; no inherited/explicit proxies | Prove DNS-to-socket binding and revalidation at every hop/retry. Client unresolved; use approved direct egress, never bypass current environment restrictions. |
| D015 | 2026-11-19, proposed; controls preserved | Whole-source batches; three attempts/180-second source and 10-minute run budgets; existing UTF-8/depth/header/byte/item limits | Recovery and transforms share budgets; 403 pauses, 429 honors Retry-After; source errors isolated. D024 adds explicit proposed full-text/node/attribute/aggregate bounds, never silent truncation. |
| D016 | 2026-11-19, proposed; boundaries preserved | Gate A names offline implementation increments; B1 authorizes bounded verification; B2 manual collection; C recurrence | Gate A approved for M1-01 only via the owner comment below; M1-02a is separately approved below; M1-02b pure helpers are separately approved below; M1-03 onward and B1/B2/C remain unapproved. |
| D017 | 2026-11-19, proposed; v1.2 metadata-first assumption superseded | Source-specific lawful basis and deadlines for complete feed/item originals, derivatives, metadata/digests and backups | D023 risk acceptance is not rights clearance. Prohibited/unresolved full-text mode blocked; written permission, applicable grants or other legally supported grounds require scope review. No metadata substitution. |
| D018 | 2026-11-19, superseded collection strategy by D022 | Historical v1.2 metadata-first vendor target; no longer the intended final capability | Original accepted decision remains in PR #6/Git history. Report-template authority, quality-reference-only Microsoft role and human control are preserved and reaffirmed in D022. |
| D019 | 2026-11-19, M1-01/M1-02a data contracts accepted; remaining design proposed | Additive V2 catalog_entry/feed_full_text modes, response/item/derived digests, availability and full-text manifests | Eligible 304 now requires intact permitted original/derived backing; v1.2 metadata-only exception no longer targets collection. V1/M1-01 unchanged; M1-02a V2/data contracts delivered by PR #9 under the approval below. Runtime semantics remain proposed. |
| D020 | 2026-11-19, proposed; transient-only assumption superseded | Authorized full-text in encrypted private storage with policy-scoped deletion of originals/derivatives/WAL/backups; no public/log leakage | Host dump/temp/swap controls and consistent isolated restore required. SQL DELETE is not verified erasure; rights expiry invalidates checkpoints. No implementation or real content fixtures. |
| D021 | 2026-11-19, open; before report tooling | Template artifact/version/license, claim-level evidence sufficiency and publication permissions | Retained source text improves reproducibility, not truth or automatic Ghana attribution. Existing template unchanged; no full articles/extensive excerpts in output. D009 review/TLP gates remain open. |
| D022 | 2026-11-19, accepted strategy only | Full-text collection from all three selected sources where authorized: complete CISA fields, Microsoft RSS content:encoded and Google RSS description; metadata-only vendor collection rejected as final target | Explicit owner task “M1 v1.3 Full-Text Collection Decision,” recorded here without a session link. Supersedes D018 collection direction and affected target assumptions in D004/D005/D008/D012/D013/D017/D019/D020. Existing report template and human workflow remain authoritative. No implementation/source-access approval. |
| D023 | 2026-11-19, accepted owner risk acknowledgement; rights clearance open | Owner reports Microsoft copying/distribution/publication and permitted-use restrictions, calls for applicable Google terms/robots review, and accepts identified operational/legal risk for private research | Owner-reported findings are not independently verified legal conclusions. Risk acceptance is not a license/exception or authority to disregard restrictions. [Open rights questions/routes](milestones/M1_EVIDENCE.md) require established lawful basis before activation. Commercial use/republication needs separate review and necessary written authorization. |
| D024 | 2026-11-23, data contracts and M1-02b identity/digest helpers accepted; transformation implementation proposed | Separate original feed HTML, sanitized HTML and plain text with independent hashes, parent links and transformation versions; explicit HTML/node/attribute/derived-byte caps | [Evidence design](milestones/M1_EVIDENCE.md) specifies inert allowlist, safe encoding/entities, no execution/resource loads, immutable transformations and bounded processing. CISA remains structured catalog content. M1-02a descriptor scope approved below; library/runtime policy/cap feasibility still needs review. No transformation code exists. |
| D025 | 2026-11-19, proposed wire bindings; delivered within M1-02a (PR #9) | Freeze the data-only contract serialization, domain labels, helper versions and explicit supplementary bounds in [contract reference](M1_EVIDENCE_CONTRACTS.md) | Prose requirements lacked exact field/domain spellings and some list bounds. M1-02b supplies separately approved canonicalization/ID/hash helpers; no runtime rights claim. Existing wire shapes and domain labels stay unchanged. |
| D026 | 2026-11-23, resolved for approved M1-02b; implementation review pending | Separate stable source revisions, versioned derivations and immutable artifact/evidence/manifest associations | [Frozen projections and namespaces](M1_IDENTITY_PROFILES.md) define source-only evidence_id, separate derived IDs, and an evidence-association key over canonical metadata. Parsed metadata and transforms cannot change an unchanged source revision. Existing wire shapes remain intact; M1-03 must use association keys rather than overwrite by evidence_id. Scope approved in the PR #15 owner comment below. |
| D027 | 2026-11-19, accepted numeric-cap amendment; Issue #10 open | RSS transferred and decoded response caps each 6 MiB; original HTML, sanitized HTML and plain-text batch aggregates each 6 MiB; per-article fields remain 1 MiB | [Owner decision](https://github.com/Ih4c/ghana-cti-pipeline/issues/10#issuecomment-7008185129) approves numeric validation changes, synthetic boundary tests and documentation under v1.3 without schema redesign. B1 measurements remain planned to confirm headroom and do not block this change. No live requests, activation or B1/B2/C approval; [capacity analysis](milestones/M1_RSS_SIZE_INVESTIGATION.md) rises to 64 MiB/day before overhead, with unchanged 2 GiB live-store and 512 MiB/day transfer caps. |

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
adapters, scheduling, deployment, publication or paid services. M1-03 and B1/B2/C
need separate approval. No contract/schema migration or report-template change.

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
