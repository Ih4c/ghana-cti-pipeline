# Project status

Last reviewed: **2026-11-18**. Verified repository: `Ih4c/ghana-cti-pipeline`.
Baseline `main`: **50224b35c1b27bbaca0fb1551bdf4b8205cb7de8**. This is a dated
snapshot, not a command to reset future work to this commit; fetch and verify
current main before each new task. PR #4's merge was independently verified on
GitHub and in Git history; it is this main commit. No subsequent main commits or
open PRs were found at readiness-review start; the working tree was clean.

## Delivered and active work

| Area | State | Evidence / next boundary |
| --- | --- | --- |
| M0 foundation | Completed | [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3); [retrospective specification](milestones/M0_FOUNDATION.md) |
| Permanent documentation structure | Completed coordination baseline | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4), merged 2026-11-18 as `50224b3`; archive, status, decisions, specifications and reusable handoff |
| M1 intelligence collection | Plan v1.1/readiness corrections proposed; **no implementation increment approved** | [Specification](milestones/M1_COLLECTION.md), [readiness review and ordered PRs](milestones/M1_READINESS.md) |
| M2–M5 | Roadmap only; not approved | [Roadmap](ROADMAP.md) |

Implemented: typed immutable contracts, validated copies, collector/storage
interfaces, dependency checks, synthetic tests, CI. Baseline: 73 passed and one
strict TLP-inheritance xfail. No real collectors, persistent evidence store,
scheduler, AI processing, public deployment or publisher exist.

## Current blockers and next action

1. Recommended next implementation is **M1-01 only, v1.1/D011**: additive core
   retrieval/observation metadata, synthetic fixtures, validation tests and related
   docs. Ready to implement only after explicit owner approval. Existing V1 and
   protocols stay unchanged; no dependencies, persistence, transport or adapters.
   Approval is not inferred from PR #4's merge or this documentation PR.
2. Vendor feed bodies, redirects, validators, sizes and anonymous runtime access
   still need separately approved bounded verification: prior feasibility checks
   hit the execution environment's outbound proxy. CISA mirror JSON/schema/license were checked
   through the GitHub connector; Microsoft/Google feed media types and official
   references were checked through the web tool. See the dated feasibility log;
   these observations were not refreshed and no sources were fetched in this review.
3. Microsoft and Google collection/retention permissions need a documented basis.
   RSS availability does not grant unrestricted copying. No vendor source is enabled.
4. D004–D008 and D011–D017 remain proposed. Approve identity rules and atomic BLOB
   storage before their respective offline increments; resolve private host/operator,
   rights/backup retention, network path/client, parser budgets and capacity before
   live work. These operational choices do not block a scoped M1-01 approval.
5. B1 authorizes only bounded source verification; B2 separately authorizes manual
   collection; C authorizes recurring scheduling. CISA is the first verification
   candidate, not an enabled source. Vendor fetching/archiving is not authorized.

## Review follow-ups

- F1/F2: implemented in PR #3 (dependency checks and validated copies).
- F3: limits are still unenforced; M1 proposes concrete fetch/text caps and tests.
- F4: TLP inheritance remains an open decision and strict xfail; blocks any exporter.
- F5: candidate V1 validation hardening (duplicates/self-lineage, dates and invisible
  text) remains separate future work; do not bundle it into M1-01 or claim it is delivered.
- F6: static type checking remains a small future tooling decision.
- F7: current URL checks are syntax-only; SSRF protection is mandatory before fetching.

Next handoff: review the exact [M1-01 approval scope](milestones/M1_READINESS.md)
and record actual owner approval or requested revisions in [DECISIONS.md](DECISIONS.md).
Until then, continue documentation only: no application changes, collector or
persistence implementation, source requests, activation, deployment, scheduling,
spending or merges. Source rights/access failures must not silently reduce the
three-source milestone scope; a single-source pilot is not milestone completion.
