# Project status

Last reviewed: **2026-11-19**. Repository: `Ih4c/ghana-cti-pipeline`.
Verified main **ccd81278472c7847287ffcf20988629435f2c999** is PR #6's merge;
Git and GitHub agree. PR #6 merged 2026-11-18. No subsequent main commits/open
PRs existed at this task's start. Always fetch current main on resumption; this
is a dated snapshot, not an instruction to reset to old history.

## Delivered and active work

| Area | State | Evidence / boundary |
| --- | --- | --- |
| M0 foundation | Completed | [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3); immutable V1, validated copies, interfaces, dependency tests and fixture CI |
| Coordination baseline | Completed | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4); permanent guidance, archive, decisions, status and reusable handoff |
| Readiness and hybrid documentation | Merged planning history | [PR #5](https://github.com/Ih4c/ghana-cti-pipeline/pull/5), [PR #6](https://github.com/Ih4c/ghana-cti-pipeline/pull/6); v1.2 metadata-first vendor strategy now superseded |
| Full-text direction | Accepted strategy only, D022 | Complete permitted CISA fields and vendor RSS articles; report template/human workflow unchanged |
| Owner risk acknowledgement | Recorded, D023; rights unresolved | Owner-reported terms findings and acceptance do not confer license, exception or permission to ignore restrictions |
| M1 v1.3 technical design | Proposed; **M1-01 and later code unapproved** | [Specification](milestones/M1_COLLECTION.md), [full-text evidence/rights design](milestones/M1_EVIDENCE.md), [PR sequence](milestones/M1_READINESS.md) |
| M2–M5 | Roadmap only | No implementation or publication approval |

Main implements only the foundation; baseline tests: 73 passing and one strict
TLP-inheritance xfail. No M1 retrieval contracts, V2 evidence, collectors, storage,
HTTP/HTML processing, scheduler or publisher are delivered. An unfinished local
v1.2 M1-01 draft was preserved separately when the owner changed scope; it is not
part of this clean documentation branch and must not be resumed as approved work.

## Blockers and decisions

1. **Documentation only now.** The owner will record any M1-01 implementation
   approval in a separate GitHub PR comment. Earlier v1.2 authorization is not
   authority for v1.3 work. Keep the first potential PR limited to offline
   retrieval/observation descriptors, synthetic tests and related documentation.
2. **Full-text rights unresolved.** Microsoft use/copying/distribution/publication
   restrictions are owner-reported and historically noted; applicable Google/
   FeedBurner terms and robots need review. Establish lawful access, retention,
   transformation, internal-use and backup basis; written permission, applicable
   grants or other legally supported grounds must cover the actual workflow.
   Risk acceptance/technical access does not clear this. Prohibited/unresolved
   full-text activation stays blocked, never silently replaced by metadata-only.
3. **Feed observations are not new runtime findings.** Owner reports Microsoft
   content:encoded and Google description complete article content on 2026-11-18.
   B1 must independently reconfirm structure/completeness/limits. Historical
   catalog/schema/CC0 checks and proxy-blocked runtime attempts remain unchanged
   in [feasibility](milestones/M1_SOURCE_FEASIBILITY.md). No source network access
   or new terms verification occurred in this revision. CISA remains the strongest
   initial verification candidate, not an enabled source.
4. **Technical choices proposed.** D004–D008, D011–D017, D019/D020 and D024 still
   need their scoped approvals. Review V2 original/derived associations, identity,
   sanitizer/encoding limits, atomic SQLite/304/reprocessing, retention and purge.
   D018 collection strategy superseded; D009/D021 remain open.
5. **Capacity and operations unresolved.** Keep 2 GiB live cap and $0 paid-service
   budget. Up to 32 MiB/day before overhead cannot fit annual retention. Explicitly
   decide lawful retention/capacity after approved measurements; never increase
   storage silently. Private host/operator, encryption/keys, backups, WAL/purge,
   one-cycle/24h budgets and publisher-stricter restrictions require verification.
6. **Reporting gates remain.** Existing report-template reference/standards unchanged;
   actual template artifact/version/license absent/unverified in this repository.
   Original human analysis may cite permitted evidence, but full articles/raw
   HTML/extensive excerpts are not public output. Facts/IOCs/TTPs still face
   applicable rights/confidentiality/review/TLP constraints; no automatic publication.

B1 verification, B2 manual activation and C scheduling each require separate
approval; none is granted. Three-source full-text completion requires all three
cleared sources or an explicit owner scope revision.

## Review follow-ups and handoff

F1/F2 delivered by PR #3. F3 input caps are still unenforced in existing V1/fetch
interfaces; full-text budgets remain proposals. F4 strict TLP xfail blocks export.
F5-wide V1 hardening/F6 tooling remain separate. F7 URL syntax is not SSRF defense;
no transport protections are implemented yet.

Follow [HANDOFF.md](HANDOFF.md) and [DECISIONS.md](DECISIONS.md). Current task ends
with a documentation-only PR for independent review. No code, source requests,
real feed fixtures, storage, deployment, schedule, paid service, reporting or merge.
