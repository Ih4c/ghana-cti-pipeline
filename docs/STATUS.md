# Project status

Last reviewed: **2026-11-19**. Repository: `Ih4c/ghana-cti-pipeline`.
Verified main **9e30ab5a3d88352f97fd7fa64ea2a676097e0e72** is
[PR #8](https://github.com/Ih4c/ghana-cti-pipeline/pull/8)'s completed merge;
Git and GitHub agree. No later main changes were present at this task's start.
Always fetch current main on resumption; this is a dated snapshot.

## Delivered and active work

| Area | State | Evidence / boundary |
| --- | --- | --- |
| M0 foundation | Completed | [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3); immutable V1, validated copies, interfaces, dependency tests and fixture CI |
| Coordination baseline | Completed | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4); permanent guidance, archive, decisions, status and reusable handoff |
| Readiness and hybrid documentation | Merged planning history | [PR #5](https://github.com/Ih4c/ghana-cti-pipeline/pull/5), [PR #6](https://github.com/Ih4c/ghana-cti-pipeline/pull/6); v1.2 metadata-first vendor strategy now superseded |
| Full-text direction | Accepted strategy only, D022 | Complete permitted CISA fields and vendor RSS articles; report template/human workflow unchanged |
| Owner risk acknowledgement | Recorded, D023; rights unresolved | Owner-reported terms findings and acceptance do not confer license, exception or permission to ignore restrictions |
| M1 v1.3 technical design | PR #7 merged; **M1-01 and M1-02a contracts approved only**, remaining design proposed | [Specification](milestones/M1_COLLECTION.md), [full-text evidence/rights design](milestones/M1_EVIDENCE.md), [PR sequence](milestones/M1_READINESS.md) |
| M1-01 implementation | Delivered by PR #8 | Five [retrieval/observation contracts](M1_RETRIEVAL_CONTRACTS.md), discriminated outcomes, synthetic fixtures/tests; no I/O |
| M1-02a implementation | Feature branch `feat/m1-02a-full-text-contracts`, pending PR review/merge | [V2 evidence, artifact, policy and manifest contracts](M1_EVIDENCE_CONTRACTS.md); synthetic tests only |
| M2–M5 | Roadmap only | No implementation or publication approval |

Verified main delivers the foundation and M1-01 (500 passed, one existing strict
TLP xfail). This branch adds M1-02a data contracts and tests; it is not delivered
on main yet. No collectors, storage, HTTP/HTML processing, scheduler or publisher
exists. The unfinished v1.2 draft remains preserved in its original worktree.

## Blockers and decisions

1. **M1-02a contract scope approved.** The
   [owner comment on PR #8](https://github.com/Ih4c/ghana-cti-pipeline/pull/8#issuecomment-6997113844)
   explicitly approves M1-02a under v1.3, covering D019/D024 data-only evidence,
   artifact-reference, provenance, source-policy and processing-manifest contracts,
   synthetic tests and documentation. Author/scope and the PR #8 merge were
   verified before application edits. All exclusions remain: no persistence,
   networking, feed processing, transforms, hash/ID generation or operations.
   This task stops at the implementation PR for independent review.
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
4. **Technical choices proposed.** D004–D008, D012–D017, D019/D024 beyond data contracts and D020 still
   need their scoped approvals. Review V2 original/derived associations, identity,
   sanitizer/encoding limits, atomic SQLite/304/reprocessing, retention and purge.
   D018 collection strategy superseded; D009/D021 remain open. D025 wire bindings
   are implemented for review; D026 source-revision versus derivation identity
   must be resolved before M1-02b, without silently changing immutable history.
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
interfaces; M1-02a validates declared full-text byte/count bounds; runtime enforcement is future work. F4 strict TLP xfail blocks export.
F5-wide V1 hardening/F6 tooling remain separate. F7 URL syntax is not SSRF defense;
no transport protections are implemented yet.

## Implementation validation and next handoff

The implementation adds five independent core modules (`evidence_values`,
`artifacts`, `evidence`, `source_policy`, `processing`), synthetic evidence fixtures,
two test modules and [contract documentation](M1_EVIDENCE_CONTRACTS.md). Existing
V1/M1-01 code and fixtures, protocols, network guard, dependency checks,
dependencies, CI configuration and report template remain unchanged.

Local Python 3.14.10: **663 passed, one existing strict TLP xfail**. Ruff lint
and format checks pass; explicit dependency tests: **15 passed**. All **133 local
Markdown links/anchors** and `git diff --check` pass. No source requests,
real feed fixtures, storage, deployment, schedule, paid service, reporting or merge
occurred. Commit author/committer must remain the required `ih4c` identity.

Follow [HANDOFF.md](HANDOFF.md) and [DECISIONS.md](DECISIONS.md). Recommended next:
**M1-02b identity and digest helpers**, after review/merge, explicit scope approval
and resolution of D026. Canonical profiles, namespaces and test vectors remain
unimplemented. Metadata validation does not verify rights, stored bytes, current
availability, repository-wide identities or conditional-checkpoint eligibility.
