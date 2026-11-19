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
| D007 | 2026-11-19, proposed; cap unchanged | Zero incremental paid-service budget and 2 GiB live-store cap, with WAL/headroom and encrypted backup accounting | Full-text response/artifact budget up to 32 MiB/day before overhead; fewer than 64 such days fit. Measure pilot and obtain explicit capacity/retention decision; no silent expansion or purchase. |
| D008 | 2026-11-19, proposed; required before collection | Preserve SSRF/TLS/proxy/request/XML/isolation controls; add full-text transformation and private artifact protection | D024 safe HTML/plain-text design is unimplemented. Real bodies may enter only an authorized private evidence store, never public Git/PR/CI/logs; this revises transient-only vendor storage assumptions. |
| D009 | 2026-11-18, open; required before exporter | Derived intelligence must not be less restrictive than its sources; resolve evidence, unknown markings and intersecting recipient restrictions | F4 strict xfail records intended CLEAR/RED rejection. Need FIRST guidance review and authenticated review/access design; not numeric TLP ordering alone. M1 has no exporter. |
| D010 | 2026-11-18, accepted coordination baseline | Permanent requirements in AGENTS/core docs; milestone versions, status/decision ledger and reusable handoff; first-task file historical | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4) merged at `50224b3`; owner explicitly designated its documentation the coordination baseline. This is not acceptance of M1 technical proposals or implementation. |
| D011 | 2026-11-19, proposed; M1-01 unapproved | Additive 200/304/failure descriptors and observations; no receipt-to-retention inference | M1-01 remains separate under v1.3 and needs owner GitHub PR-comment approval. Existing V1/protocols unchanged; descriptor-only scope excludes V2, hashing, I/O and later increments. |
| D012 | 2026-11-19, proposed; source/transform identity revision | Immutable source revisions include original selected article content; transformations have separate versioned derivation identities | Original changes matter even if sanitized output is unchanged. Reuse available A in A→B→A via chronological observations, never edit parent/history or resurrect revoked/deleted content. |
| D013 | 2026-11-19, proposed; full-text revision | Atomic SQLite response/original/derived/evidence/manifest/checkpoint BLOB transactions | BLOBs simplify recovery but amplify storage/WAL/backups. Separate artifacts deferred pending measured need and explicit design. Required derivation failure rolls back whole source batch. |
| D014 | 2026-11-18, proposed; unchanged | Direct-only validated-IP connections with original-host TLS; manual validated redirects; no inherited/explicit proxies | Prove DNS-to-socket binding and revalidation at every hop/retry. Client unresolved; use approved direct egress, never bypass current environment restrictions. |
| D015 | 2026-11-19, proposed; controls preserved | Whole-source batches; three attempts/180-second source and 10-minute run budgets; existing UTF-8/depth/header/byte/item limits | Recovery and transforms share budgets; 403 pauses, 429 honors Retry-After; source errors isolated. D024 adds explicit proposed full-text/node/attribute/aggregate bounds, never silent truncation. |
| D016 | 2026-11-19, proposed; boundaries preserved | Gate A names offline implementation increments; B1 authorizes bounded verification; B2 manual collection; C recurrence | No gate approved under v1.3. Strategy/risk acknowledgement is neither vendor permission nor implementation approval. Owner will record any M1-01 approval in a separate GitHub PR comment. |
| D017 | 2026-11-19, proposed; v1.2 metadata-first assumption superseded | Source-specific lawful basis and deadlines for complete feed/item originals, derivatives, metadata/digests and backups | D023 risk acceptance is not rights clearance. Prohibited/unresolved full-text mode blocked; written permission, applicable grants or other legally supported grounds require scope review. No metadata substitution. |
| D018 | 2026-11-19, superseded collection strategy by D022 | Historical v1.2 metadata-first vendor target; no longer the intended final capability | Original accepted decision remains in PR #6/Git history. Report-template authority, quality-reference-only Microsoft role and human control are preserved and reaffirmed in D022. |
| D019 | 2026-11-19, proposed; full-text revision | Additive V2 catalog_entry/feed_full_text modes, response/item/derived digests, availability and full-text manifests | Eligible 304 now requires intact permitted original/derived backing; v1.2 metadata-only exception no longer targets collection. V1 shapes/excerpts unchanged; no V2 implementation. |
| D020 | 2026-11-19, proposed; transient-only assumption superseded | Authorized full-text in encrypted private storage with policy-scoped deletion of originals/derivatives/WAL/backups; no public/log leakage | Host dump/temp/swap controls and consistent isolated restore required. SQL DELETE is not verified erasure; rights expiry invalidates checkpoints. No implementation or real content fixtures. |
| D021 | 2026-11-19, open; before report tooling | Template artifact/version/license, claim-level evidence sufficiency and publication permissions | Retained source text improves reproducibility, not truth or automatic Ghana attribution. Existing template unchanged; no full articles/extensive excerpts in output. D009 review/TLP gates remain open. |
| D022 | 2026-11-19, accepted strategy only | Full-text collection from all three selected sources where authorized: complete CISA fields, Microsoft RSS content:encoded and Google RSS description; metadata-only vendor collection rejected as final target | Explicit owner task “M1 v1.3 Full-Text Collection Decision,” recorded here without a session link. Supersedes D018 collection direction and affected target assumptions in D004/D005/D008/D012/D013/D017/D019/D020. Existing report template and human workflow remain authoritative. No implementation/source-access approval. |
| D023 | 2026-11-19, accepted owner risk acknowledgement; rights clearance open | Owner reports Microsoft copying/distribution/publication and permitted-use restrictions, calls for applicable Google terms/robots review, and accepts identified operational/legal risk for private research | Owner-reported findings are not independently verified legal conclusions. Risk acceptance is not a license/exception or authority to disregard restrictions. [Open rights questions/routes](milestones/M1_EVIDENCE.md) require established lawful basis before activation. Commercial use/republication needs separate review and necessary written authorization. |
| D024 | 2026-11-19, proposed | Separate original feed HTML, sanitized HTML and plain text with independent hashes, parent links and transformation versions; explicit HTML/node/attribute/derived-byte caps | [Evidence design](milestones/M1_EVIDENCE.md) specifies inert allowlist, safe encoding/entities, no execution/resource loads, immutable transformations and bounded processing. CISA remains structured catalog content. Library/policy/cap feasibility needs approval/tests; no transformation code exists. |

## Current authorization and stopping point — 2026-11-19

The owner explicitly requested a documentation-only v1.3 PR and directed:

> Do not implement any code. No implementation, source-access or operational
> approval is granted.
>
> Keep M1-01 as a separate, unapproved implementation increment.
>
> The owner will record any M1-01 implementation approval separately in a
> GitHub PR comment. Do not infer that approval from this instruction.

This version-controlled record transcribes the supplied task; it does not invent
a GitHub approval URL. The v1.3 instruction supersedes continuation of the earlier
v1.2 M1-01 request. An unfinished local draft was preserved outside this documentation
branch; it is not delivered or authorized to continue under this task.

- Specification: M1_COLLECTION.md v1.3, M1_EVIDENCE.md design v1.1 and
  M1_READINESS.md review v1.2. Technical proposals only.
- Accepted: D022 strategy and D023 owner risk acknowledgement only, not rights clearance.
- Superseded: D018's vendor metadata-first target and affected v1.2 assumptions as recorded above.
- Implementation approval: **none under v1.3**, including M1-01.
- Source verification B1, manual activation B2, recurrence C: **not approved**.
- Next authorized action: review this documentation PR. Any later code approval
  must be recorded separately by the owner in a GitHub PR comment with exact scope/version.
- No collector/storage/transport/transform implementation, network/source requests,
  deployment, schedule, spending, report generation, publication or merge is authorized.
