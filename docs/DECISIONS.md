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
| D004 | 2026-11-18, proposed | M1 v1.0: CISA KEV JSON, Microsoft Security Blog RSS, Google Threat Intelligence/Mandiant RSS; feed-only vendor content, no article crawler | [Feasibility evidence](milestones/M1_SOURCE_FEASIBILITY.md). Rights/runtime checks are incomplete; no activation approval. All three remain candidates. |
| D005 | 2026-11-18, proposed | Private SQLite plus bounded content-addressed response storage; retrieval/observation ledger outside existing immutable evidence records | [M1 architecture](milestones/M1_COLLECTION.md). Retains exact transport provenance and source revisions without mutating V1 records. No backend exists yet. |
| D006 | 2026-11-18, proposed | Manual CLI first; after explicit activation, one daily local timer on an approved private host; GitHub Actions remains fixture CI | Avoid public evidence/log leakage and hosted-runner persistence problems. No new host purchased or timer enabled. |
| D007 | 2026-11-18, proposed | Zero incremental paid-service budget on existing hardware; caps, retention and encrypted backups per M1; paid hosting requires separate approval | Needs named operator (role/handle only), host validation and an approved storage location. Retention must honor source permissions. |
| D008 | 2026-11-18, proposed; required before collection | Fetch-time SSRF defense, XML/size limits, bounded retries and per-source isolation | Closes F3/F7 operational gaps. Current schema URL validation does not provide network safety. |
| D009 | 2026-11-18, open; required before exporter | Derived intelligence must not be less restrictive than its sources; resolve evidence, unknown markings and intersecting recipient restrictions | F4 strict xfail records intended CLEAR/RED rejection. Need FIRST guidance review and authenticated review/access design; not numeric TLP ordering alone. M1 has no exporter. |
| D010 | 2026-11-18, proposed governance | Permanent requirements in AGENTS/core docs; per-milestone versions, status/approval ledger and reusable handoff; first-task file historical only | This documentation PR proposes the structure. Acceptance of governance does not approve M1 implementation or activation. |

## Approval record to complete before M1 implementation

- Specification: M1_COLLECTION.md v1.0 (or revised version).
- Implementation approval: **pending**.
- Approved scope/conditions: **none recorded**.
- Approval reference: **pending owner review**; use a PR review/comment or other
  durable repository record, never a session link.
- Source activation: **not approved**; record separate source-specific rights,
  endpoint/host checks and operational authorization before live collection.

If an approval arrives outside GitHub, carry its exact scope into a documentation
change for traceability, using only the permitted handle. Do not invent a URL or
claim that a reviewer approved conditions they did not address.
