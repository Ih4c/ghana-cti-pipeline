# Project status

Last reviewed: **2026-11-18**. Verified repository: `Ih4c/ghana-cti-pipeline`.
Baseline `main`: **8d3dff3cea24b7b9007cf2f5824824da773bcc85**. This is a dated
snapshot, not a command to reset future work to this commit; fetch and verify
current main before each new task. The working tree was clean at planning start.

## Delivered and active work

| Area | State | Evidence / next boundary |
| --- | --- | --- |
| M0 foundation | Completed | [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3); [retrospective specification](milestones/M0_FOUNDATION.md) |
| Permanent documentation structure | Proposed in this documentation PR | Archive old first-task instructions; establish status, decisions, specifications and handoff |
| M1 intelligence collection | Plan v1.0 proposed; **implementation not approved** | [Specification](milestones/M1_COLLECTION.md), [source feasibility](milestones/M1_SOURCE_FEASIBILITY.md) |
| M2–M5 | Roadmap only; not approved | [Roadmap](ROADMAP.md) |

Implemented: typed immutable contracts, validated copies, collector/storage
interfaces, dependency checks, synthetic tests, CI. Baseline: 73 passed and one
strict TLP-inheritance xfail. No real collectors, persistent evidence store,
scheduler, AI processing, public deployment or publisher exist.

## Current blockers and next action

1. Owner must approve the exact M1 specification version and implementation scope
   before collector code begins. Planning approval and source activation are
   separate; no approval is inferred from merging these docs.
2. Vendor feed bodies, redirects, validators, sizes and anonymous runtime access
   still need bounded verification: this execution environment's outbound proxy
   rejects direct endpoint requests. CISA mirror JSON/schema/license were checked
   through the GitHub connector; Microsoft/Google feed media types and official
   references were checked through the web tool. See the dated feasibility log.
3. Microsoft and Google collection/retention permissions need a documented basis.
   RSS availability does not grant unrestricted copying. No vendor source is enabled.
4. Choose the private host/operator, retention, resource limits and budgets in
   D004–D008. Confirm access checks from that host before any live run.

## Review follow-ups

- F1/F2: implemented in PR #3 (dependency checks and validated copies).
- F3: limits are still unenforced; M1 proposes concrete fetch/text caps and tests.
- F4: TLP inheritance remains an open decision and strict xfail; blocks any exporter.
- F5: candidate validation hardening (duplicates/self-lineage, dates and invisible
  text). Evaluate in the approved contract increment; do not claim it is delivered.
- F6: static type checking remains a small future tooling decision.
- F7: current URL checks are syntax-only; SSRF protection is mandatory before fetching.

Next handoff: review [M1_COLLECTION.md](milestones/M1_COLLECTION.md) and record
explicit approval or requested revisions in [DECISIONS.md](DECISIONS.md). Continue
documentation/feasibility only until approval. Source rights or access failures
must not silently reduce the three-source acceptance scope; revise it for review.
