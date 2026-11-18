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
| D004 | 2026-11-18, proposed technical onboarding | M1 v1.2 maps CISA to permitted raw-backed catalog data and both vendor RSS feeds to metadata-first projections; no article crawler | D018 accepts the strategy only. Endpoint, exact fields, transient-processing/retention permissions and runtime access remain unapproved. [Source policies](milestones/M1_EVIDENCE.md). |
| D005 | 2026-11-18, proposed | Private SQLite with explicit V1/V2 lookup, retrieval/observation/manifest ledger and optional policy-permitted raw artifacts | D013/D019 revise the all-snapshot assumption: metadata-only acquisitions have no artifact. No backend exists; V1 interfaces remain unchanged. |
| D006 | 2026-11-18, proposed | Manual CLI first; separately approved daily timer on a private host; fixture-only Actions | Hybrid modes share the same isolated runner. B1 verification, B2 manual collection and C scheduling remain separate under D016. No host or schedule enabled. |
| D007 | 2026-11-18, proposed | Zero incremental paid-service budget, capacity stop limits and encrypted private backups | Metadata-first reduces storage, not transfer volume. Even CISA maximum daily snapshots exceed 2 GiB/year. Host/operator, measured growth, backup/purge feasibility and source deadlines remain live-readiness gates. |
| D008 | 2026-11-18, proposed; required before collection | Preserve SSRF, parser/input caps, retry budgets and source isolation; prevent vendor raw-data leakage on every path | D014/D015 controls unchanged; D020 adds typed storage projections, transient-only vendor bodies, no raw diagnostics/spooling and host dump/swap verification. Schema checks do not provide network safety. |
| D009 | 2026-11-18, open; required before exporter | Derived intelligence must not be less restrictive than its sources; resolve evidence, unknown markings and intersecting recipient restrictions | F4 strict xfail records intended CLEAR/RED rejection. Need FIRST guidance review and authenticated review/access design; not numeric TLP ordering alone. M1 has no exporter. |
| D010 | 2026-11-18, accepted coordination baseline | Permanent requirements in AGENTS/core docs; milestone versions, status/decision ledger and reusable handoff; first-task file historical | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4) merged at `50224b3`; owner explicitly designated its documentation the coordination baseline. This is not acceptance of M1 technical proposals or implementation. |
| D011 | 2026-11-18, proposed; revised for v1.2 | Additive 200/304/failure descriptors and observations; ResponseBodyMetadata replaces unimplemented SnapshotRef in M1-01 | Receipt/digest does not imply retention. D019 separates descriptors from later artifact/manifest associations. Existing V1/protocols unchanged. Approval needed for M1-01 and only the descriptor portion of D019. |
| D012 | 2026-11-18, proposed; refined for hybrid evidence | Canonical retained-field/profile identity, native-key-kind separation, immutable revision reuse and chronological observations | Metadata equality is not article equality. Response digest separate; representation/projection change creates new profile/revision. A→B→A reuses available A; no tombstone resurrection. Exact constants/vectors in M1-02b. |
| D013 | 2026-11-18, proposed | SQLite atomic evidence/manifest/observation/checkpoint commits with optional permitted raw BLOBs | Retains v1.1 single-resource recovery simplification; raw artifact required only in raw-backed mode. Metadata-only API cannot accept raw bytes. D019 governs 304 integrity; D020 governs expiry/restore. |
| D014 | 2026-11-18, proposed; unchanged | Direct-only validated-IP connections with original-host TLS; manual validated redirects; no inherited/explicit proxies | Prove DNS-to-socket binding and revalidation at every hop/retry. Client unresolved; use approved direct egress, never bypass current environment restrictions. |
| D015 | 2026-11-18, proposed; retained | Whole-source batch acceptance; 180-second budget including all delays/fallback, maximum three attempts; UTF-8, depth 64, headers 32 KiB and existing byte/item/text caps | Ignoring embedded articles does not bypass caps. No raw vendor quarantine; rejected batch leaves checkpoint unchanged and other sources run. |
| D016 | 2026-11-18, proposed; unchanged | Gate A names offline implementation increments; B1 authorizes bounded verification; B2 manual collection; C recurrence | No gate approved. Hybrid strategy acceptance is neither vendor permission nor implementation approval. Each gate records its exact scope and durable reference. |
| D017 | 2026-11-18, proposed; blanket archive prerequisite revised by D018 | Source-specific permissions for transient processing, retained fields/excerpts/digests and backups; cap is a stop condition | v1.1 assumed full-feed retention or deferral. v1.2 instead proposes metadata-first vendor collection, subject to its own permissions; zero durable vendor raw retention. D020 defines deletion/backup requirements; no universal 365-day vendor entitlement. |
| D018 | 2026-11-18, accepted strategic direction only | Hybrid collection: permitted CISA structured/raw data; metadata-first Microsoft/Google with justified permitted excerpts; no default vendor raw archive or article crawling. Existing report template authoritative; Microsoft reference improves quality only | Explicit owner task “Finalize the Ghana CTI Pipeline's Hybrid Collection Strategy,” transcribed here for version-controlled traceability; no session link. Preserves human attribution, Ghana claims, final judgment and publication. Does not approve schemas, increments, rights, operations or a template redesign. |
| D019 | 2026-11-18, proposed | Additive hybrid EvidenceRevisionV2, distinct response/retained digests, explicit availability, manifests and mode-aware 304 eligibility | [Hybrid model](milestones/M1_EVIDENCE.md). No fake V1 excerpts; metadata-only 304 requires intact permitted projections/manifest, not raw bytes. M1-01 covers descriptors only; evidence V2 and state logic remain later approvals. |
| D020 | 2026-11-18, proposed | Transient vendor bodies only; source-specific deadlines, typed projection boundary, leak tests, verified purge and isolated restore | No raw vendor DB/WAL/log/backup/test capture. Policy covers hashes/tombstones too. Host swap/dumps and SQLite/backup erasure must be validated; SQL DELETE alone insufficient. No retention implementation now. |
| D021 | 2026-11-18, open; before report tooling | Claim-level evidence sufficiency and analyst verification; confirm authoritative external template artifact/version and license | Checked-in reporting standards reference but do not contain the template. Metadata/digests cannot reproduce an unretained article. [Compatibility assessment](milestones/M1_EVIDENCE.md) preserves existing requirements; no replacement, reporting code or exporter. |

## Approval record to complete before M1 implementation

- Specification: M1_COLLECTION.md v1.2, M1_READINESS.md review v1.1 and
  M1_EVIDENCE.md design v1.0: technical proposals; D018 strategy accepted only.
- Strategic direction: **D018 accepted by explicit owner instruction**; this
  document records that scope, not an inferred implementation authorization.
- Implementation approval: **pending**.
- Approved scope/conditions: **none recorded**.
- Requested next scope: **M1-01 only / revised D011 and D019 descriptors** — additive metadata contracts,
  synthetic fixtures, offline tests and related docs. No V1/interface changes,
  new dependencies, V2 evidence implementation, hashing behavior, persistence,
  transport, parsers, adapters or live operations.
- Approval reference: **pending owner review**; use a PR review/comment or other
  durable repository record, never a session link.
- Source verification B1, manual activation B2 and scheduling C: **not approved**;
  record separate source-specific rights, endpoint/host checks and authorization.

If an approval arrives outside GitHub, carry its exact scope into a documentation
change for traceability, using only the permitted handle. Do not invent a URL or
claim that a reviewer approved conditions they did not address.
