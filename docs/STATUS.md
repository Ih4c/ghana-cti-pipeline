# Project status

Last reviewed: **2026-11-18**. Verified repository: `Ih4c/ghana-cti-pipeline`.
Baseline main: **1e5c2bca28077406acae576b88e77114f1288450**. This dated snapshot
is not a command to reset future work; fetch and verify current main each task.
Git/GitHub confirm PR #4 merged at `50224b3` and PR #5 merged at `1e5c2bc`.
No later main commits or open PRs existed at hybrid-review start; tree was clean.

## Delivered and active work

| Area | State | Evidence / boundary |
| --- | --- | --- |
| M0 foundation | Completed | [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3); [M0 retrospective](milestones/M0_FOUNDATION.md) |
| Coordination baseline | Completed | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4): archive, permanent guidance, status, decisions, specifications and reusable handoff |
| M1 readiness documentation | Merged, technical proposals unapproved | [PR #5](https://github.com/Ih4c/ghana-cti-pipeline/pull/5), 2026-11-18; v1.1/readiness review, no implementation delivered |
| Hybrid strategic direction | Accepted only at strategy level, D018 | Explicit owner task: CISA permitted raw data; metadata-first vendor feeds; existing report template preserved; human judgment/publication |
| M1 technical design | v1.2 proposed; **no increment approved** | [Specification](milestones/M1_COLLECTION.md), [hybrid evidence/retention/reporting assessment](milestones/M1_EVIDENCE.md), [execution plan](milestones/M1_READINESS.md) |
| M2–M5 | Roadmap only; not approved | [Roadmap](ROADMAP.md) |

Implemented: immutable V1 contracts with validated copies, collector/storage
interfaces, dependency checks, synthetic tests and CI. Baseline: 73 passing tests
and one strict TLP-inheritance xfail. No hybrid V2 contracts, real collectors,
persistent backend, scheduler, AI processing, report generator or publisher exist.

## Current blockers and next action

1. First recommendation: **M1-01 only under v1.2 / revised D011 and the descriptor
   portion of D019**. Add offline retrieval/observation contracts that distinguish
   receiving/hashing bytes from retaining them, synthetic fixtures and tests.
   Preserve V1/excerpt rules and protocols; no new dependencies or V2 evidence
   implementation, hashing behavior, storage, transport or parsers. Explicit owner
   approval remains required; strategy acceptance and PR merges are not approval.
2. D004–D008, D011–D017 and D019/D020 remain technical proposals. Approve later
   V2 evidence, projection/identity, mode-aware 304s, SQLite and lifecycle choices
   only in their scoped increments. All source activation remains off.
3. Vendor metadata and transient parsing still need permissions; optional excerpts
   need field/length/use justification. No default raw feed archive. Historical
   feasibility remains unchanged: CISA catalog/schema/CC0 checked via connector;
   vendor payloads and anonymous runtime checks incomplete. No source requests or
   vendor content retrieval occurred in this hybrid review. CISA is the strongest
   first verification candidate, not an enabled source.
4. Before live work: approve private host/operator, permitted direct egress,
   parser/client behavior, memory/dump protections, per-class retention deadlines,
   backup expiry/purge/restore, quotas and measured capacity. Metadata collection
   is not automatically exempt from terms; response hashes are not archived bodies.
5. B1 permits bounded source verification only, B2 separately permits manual
   collection, C recurring scheduling. None approved. All three sources or an
   explicit scope revision are required for milestone completion.
6. D021 records reporting gaps: the referenced authoritative template is not
   included in this checkout; its version/license and field-level compatibility
   remain to verify before report tooling. Vendor metadata alone cannot support
   detailed article claims. The reporting standards/template reference remain
   unchanged. D009 inheritance and authenticated publication review remain open.

## Review follow-ups

- F1/F2 delivered by PR #3: dependency-direction checks and validated copies.
- F3: existing V1/fetch limits still unenforced; proposed M1 boundary tests required.
- F4: TLP inheritance remains a strict xfail; blocks any exporter.
- F5 broad V1 validation cleanup and F6 type-checker tooling remain separate work.
- F7: URL syntax checks are not SSRF protection; transport controls unimplemented.

Handoff: follow [HANDOFF.md](HANDOFF.md), review the exact M1-01 scope and record
actual approval in [DECISIONS.md](DECISIONS.md). Current authorized work is
**documentation only**. No code, source requests, persistence, scheduling,
deployment, publication, spending or merges are authorized by this review.
