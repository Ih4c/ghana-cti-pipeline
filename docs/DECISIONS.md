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
| D004 | 2026-11-18, proposed | M1 v1.1 retains v1.0's CISA KEV JSON, Microsoft Security Blog RSS, Google Threat Intelligence/Mandiant RSS candidates; no article crawler | [Feasibility evidence](milestones/M1_SOURCE_FEASIBILITY.md) is unchanged. Rights/runtime checks are incomplete; D017 clarifies full-feed retention. No activation approval. |
| D005 | 2026-11-18, proposed | Private SQLite, content-addressed response storage and separate retrieval/observation ledger | v1.0 proposed a snapshot directory. D013 explicitly proposes BLOBs in SQLite instead; D011/D012 refine compatibility and identity. All remain proposals; no backend exists. |
| D006 | 2026-11-18, proposed | Manual CLI first; after explicit activation, one daily local timer on an approved private host; GitHub Actions remains fixture CI | Avoid public evidence/log leakage and hosted-runner persistence problems. No new host purchased or timer enabled. |
| D007 | 2026-11-18, proposed | Zero incremental paid-service budget on existing hardware; caps, retention and encrypted backups per M1; paid hosting requires separate approval | Needs named operator (role/handle only), host validation and an approved storage location. Retention must honor source permissions. |
| D008 | 2026-11-18, proposed; required before collection | Fetch-time SSRF defense, XML/size limits, bounded retries and per-source isolation | D014/D015 specify the proposed connection/parser/batch policies. Current schema URL validation does not provide network safety; no operational controls are implemented. |
| D009 | 2026-11-18, open; required before exporter | Derived intelligence must not be less restrictive than its sources; resolve evidence, unknown markings and intersecting recipient restrictions | F4 strict xfail records intended CLEAR/RED rejection. Need FIRST guidance review and authenticated review/access design; not numeric TLP ordering alone. M1 has no exporter. |
| D010 | 2026-11-18, accepted coordination baseline | Permanent requirements in AGENTS/core docs; milestone versions, status/decision ledger and reusable handoff; first-task file historical | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4) merged at `50224b3`; owner explicitly designated its documentation the coordination baseline. This is not acceptance of M1 technical proposals or implementation. |
| D011 | 2026-11-18, proposed | Additive typed 200/304/failure retrieval metadata, SnapshotRef and EvidenceObservation; existing V1 models/protocols unchanged | [M1-01 specification](milestones/M1_READINESS.md). A 304 references a committed 200 and contains no body; cross-record validation belongs to storage. First increment needs only this decision and scoped Gate A approval. |
| D012 | 2026-11-18, proposed | Versioned canonical identity profile; reuse immutable evidence, track later retrievals and A→B→A chronologically outside evidence parent links | Corrects deterministic ID versus mutable retrieval-time conflict. Namespace constants/golden vectors and exact per-adapter field projections required before storage/integration. |
| D013 | 2026-11-18, proposed alternative to v1.0 layout | Store bounded snapshots as SQLite BLOBs; atomically commit snapshot/evidence/observations/checkpoint | Removes two-resource commit and orphan-file recovery from M1. Needs separate storage approval, failure injection, consistent backup/restore and schema compatibility tests. |
| D014 | 2026-11-18, proposed | Direct-only validated-IP connections with original-host TLS; manual validated redirects; no inherited or explicit proxy support | Must prove DNS-to-socket binding with injected tests before transport acceptance. Client choice unresolved; an approved host is required, not a bypass of the current environment proxy. |
| D015 | 2026-11-18, proposed | Whole-source batch acceptance; 180-second source budget including backoff/redirects/fallback; UTF-8, depth 64 and 32 KiB header limits | Simplifies partial replay/quarantine and makes runtime bounds testable. Three attempts maximum and existing byte/item caps remain; invalid source batches leave checkpoints unchanged and other sources run. |
| D016 | 2026-11-18, proposed | Gate A may authorize named offline increments; B1 authorizes bounded verification; B2 manual collection; C recurring scheduling | Removes the circular requirement for completed runtime verification before the verification request itself. All approvals pending; synthetic work needs no production host/rights but still needs explicit implementation approval. |
| D017 | 2026-11-18, proposed | Rights cover complete retained feeds and backup lifetimes; capacity cap is a stop condition, not a retention guarantee | Defer vendor fetching if full-feed permission is absent; no synthetic excerpt or silent metadata-only fallback. Pilot growth/host/operator/backup policy remain live-readiness gates. |

## Approval record to complete before M1 implementation

- Specification: M1_COLLECTION.md v1.1 and M1_READINESS.md review v1.0, both proposed.
- Implementation approval: **pending**.
- Approved scope/conditions: **none recorded**.
- Requested next scope: **M1-01 only / D011** — additive metadata contracts,
  synthetic fixtures, offline tests and related docs. No V1/interface changes,
  new dependencies, persistence, transport, parsers, adapters or live operations.
- Approval reference: **pending owner review**; use a PR review/comment or other
  durable repository record, never a session link.
- Source verification B1, manual activation B2 and scheduling C: **not approved**;
  record separate source-specific rights, endpoint/host checks and authorization.

If an approval arrives outside GitHub, carry its exact scope into a documentation
change for traceability, using only the permitted handle. Do not invent a URL or
claim that a reviewer approved conditions they did not address.
