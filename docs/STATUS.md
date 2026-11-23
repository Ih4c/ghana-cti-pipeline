# Project status

Last reviewed: **2026-11-23**. Repository: `Ih4c/ghana-cti-pipeline`.
Application contracts delivered by [PR #9](https://github.com/Ih4c/ghana-cti-pipeline/pull/9) (M1-02a),
with D027 numeric caps delivered by [PR #15](https://github.com/Ih4c/ghana-cti-pipeline/pull/15);
documentation follow-ups [PR #12](https://github.com/Ih4c/ghana-cti-pipeline/pull/12)
and [PR #13](https://github.com/Ih4c/ghana-cti-pipeline/pull/13), and the RSS investigation
[PR #14](https://github.com/Ih4c/ghana-cti-pipeline/pull/14), are merged.
Verified against GitHub on 2026-11-23: main was `0638c5e` (the PR #15 merge). This
is a dated snapshot, so always fetch current main on resumption and treat the PR
list as the source of truth for what is delivered.

## Delivered and active work

| Area | State | Evidence / boundary |
| --- | --- | --- |
| M0 foundation | Completed | [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3); immutable V1, validated copies, interfaces, dependency tests and fixture CI |
| Coordination baseline | Completed | [PR #4](https://github.com/Ih4c/ghana-cti-pipeline/pull/4); permanent guidance, archive, decisions, status and reusable handoff |
| Readiness and hybrid documentation | Merged planning history | [PR #5](https://github.com/Ih4c/ghana-cti-pipeline/pull/5), [PR #6](https://github.com/Ih4c/ghana-cti-pipeline/pull/6); v1.2 metadata-first vendor strategy now superseded |
| Full-text direction | Accepted strategy only, D022 | Complete permitted CISA fields and vendor RSS articles; report template/human workflow unchanged |
| Owner risk acknowledgement | Recorded, D023; rights unresolved | Owner-reported terms findings and acceptance do not confer license, exception or permission to ignore restrictions |
| M1 v1.3 technical design | PR #7 merged; **M1-01/M1-02a contracts and M1-02b pure helpers approved**, remaining design proposed | [Specification](milestones/M1_COLLECTION.md), [full-text evidence/rights design](milestones/M1_EVIDENCE.md), [PR sequence](milestones/M1_READINESS.md) |
| M1-01 implementation | Delivered by PR #8 | Five [retrieval/observation contracts](M1_RETRIEVAL_CONTRACTS.md), discriminated outcomes, synthetic fixtures/tests; no I/O |
| M1-02a implementation | Delivered by [PR #9](https://github.com/Ih4c/ghana-cti-pipeline/pull/9) | [V2 evidence, artifact, policy and manifest contracts](M1_EVIDENCE_CONTRACTS.md); synthetic tests only |
| Documentation consistency | PR #12 and PR #13 merged; Issue #11 closed | Current-state sync and permanent pre-PR SHA/PR-state/test-count checks delivered; historical milestone references preserved |
| RSS size investigation | Delivered by PR #14; Issue #10 open | [Limits, B1 measurement plan and decision matrix](milestones/M1_RSS_SIZE_INVESTIGATION.md); actual sizes/headroom unmeasured |
| D027 numeric-cap amendment | Delivered by PR #15 | RSS response and each representation aggregate 6 MiB, article fields 1 MiB; synthetic boundary tests only; no B1/B2/C approval |
| M1-02b identities/digests | Approved; implemented on this feature branch for review | [Profiles, namespaces and D026 resolution](M1_IDENTITY_PROFILES.md), pure helpers, synthetic vectors and supplied-record checks; no I/O |
| M2–M5 | Roadmap only | No implementation or publication approval |

Main delivers the foundation, M1-01, M1-02a and D027 (667 passed, one existing strict
TLP xfail). No collectors, storage, HTTP/HTML processing, scheduler or publisher
exists. The unfinished v1.2 draft remains preserved in its original worktree.

## Blockers and decisions

1. **M1-02b pure helper scope approved.** The
   [owner comment on PR #15](https://github.com/Ih4c/ghana-cti-pipeline/pull/15#issuecomment-7008787831)
   approves M1-02b under v1.3: D012/D024 identity and digest helpers, D026 resolution,
   canonicalization, UUIDv5, SHA-256, synthetic golden vectors, tests and docs.
   Author/scope were verified before application changes and rechecked 2026-11-23.
   Preserve existing wire shapes, D027 caps and Issue #10. No persistence, network,
   parsing, sanitization, adapters or operations. M1-03 onward needs fresh approval.
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
4. **Technical choices proposed.** D004–D008, D013–D017, D019/D024 beyond contracts/pure helpers and D020 still
   need their scoped approvals. Review V2 original/derived associations, identity,
   sanitizer/encoding limits, atomic SQLite/304/reprocessing, retention and purge.
   D018 collection strategy superseded; D009/D021 remain open. D025 wire bindings
   are delivered by PR #9; D026 source-revision versus derivation identity
   is resolved in the [profile specification](M1_IDENTITY_PROFILES.md). Review
   its exact projections and association keys before M1-03; storage semantics and
   lifecycle enforcement remain unimplemented.
5. **Capacity and operations unresolved.** Keep 2 GiB live cap and $0 paid-service
   budget. Up to 64 MiB/day before overhead cannot fit annual retention. Explicitly
   decide lawful retention/capacity after approved measurements; never increase
   storage silently. Private host/operator, encryption/keys, backups, WAL/purge,
   one-cycle/24h budgets and publisher-stricter restrictions require verification.
6. **Reporting gates remain.** Existing report-template reference/standards unchanged;
   actual template artifact/version/license absent/unverified in this repository.
   Original human analysis may cite permitted evidence, but full articles/raw
   HTML/extensive excerpts are not public output. Facts/IOCs/TTPs still face
   applicable rights/confidentiality/review/TLP constraints; no automatic publication.
7. **RSS size uncertainty remains open.** [#10](https://github.com/Ih4c/ghana-cti-pipeline/issues/10)
   needs actual transferred/decoded byte measurements over several days. The
   [owner decision](https://github.com/Ih4c/ghana-cti-pipeline/issues/10#issuecomment-7008185129)
   accepts D027: raise both RSS response counters and each representation batch
   aggregate to 6 MiB; retain 1 MiB per article and the generic 8 MiB ceiling.
   Numeric implementation and synthetic tests are approved without waiting for B1;
   reported truncated character counts still establish no byte headroom. The
   [investigation](milestones/M1_RSS_SIZE_INVESTIGATION.md) preserves the future
   B1 procedure. No live measurement, harness or source activation is approved.
   [#11](https://github.com/Ih4c/ghana-cti-pipeline/issues/11) is **closed** after
   PR #13 completed the permanent documentation-consistency rule; PR #12 delivered
   its preceding status sync. Continue that rule after every merge.

B1 verification, B2 manual activation and C scheduling each require separate
approval; none is granted. Three-source full-text completion requires all three
cleared sources or an explicit owner scope revision.

## Review follow-ups and handoff

F1/F2 delivered by PR #3. F3 input caps are still unenforced in existing V1/fetch
interfaces; M1-02a validates declared full-text byte/count bounds; runtime enforcement is future work. F4 strict TLP xfail blocks export.
F5-wide V1 hardening/F6 tooling remain separate. F7 URL syntax is not SSRF defense;
no transport protections are implemented yet.

## Delivered validation and next handoff

PR #9 added five independent core modules (`evidence_values`,
`artifacts`, `evidence`, `source_policy`, `processing`), synthetic evidence fixtures,
two test modules and [contract documentation](M1_EVIDENCE_CONTRACTS.md). Existing
V1/M1-01 code and fixtures, protocols, network guard, dependency checks,
dependencies, CI configuration and report template remain unchanged.

PR #9 validation, local Python 3.14.10: **663 passed, one existing strict TLP xfail**. Ruff lint
and format checks pass; explicit dependency tests: **15 passed**. All **133 local
Markdown links/anchors** and `git diff --check` pass. No source requests,
real feed fixtures, storage, deployment, schedule, paid service, reporting or merge
occurred. Commit author/committer must remain the required `ih4c` identity.

PR #14's Issue #10 documentation review on 2026-11-19 re-ran the unchanged main suite:
**663 passed, one existing strict TLP xfail**, Ruff lint/format passed. No new test
code or source requests were authorized or performed in that PR. D027's subsequent
owner approval supersedes only its recommendation to retain 2 MiB pending B1.

PR #15 changed numeric validation in `evidence`/`processing` and their
synthetic tests. Schema versions, serialized shapes, generic receipt/artifact and
per-article bounds, V1/protocols, dependencies and the report template stay unchanged.
Capacity calculations now allow 64 MiB/day before overhead, fewer than 32 full-size
days in the unchanged 2 GiB store; primary body transfer is 20 MiB/day, at most
60 MiB/day across three attempts before ancillary traffic. The 512 MiB/day transfer
cap and $0 paid-service budget remain. No runtime enforcement or measured headroom
is claimed; no live requests or operational actions occurred.

PR #15 validation: **667 passed, one existing strict TLP xfail**; Ruff lint
and format passed, explicit boundary suite **15 passed**, **152 local Markdown
links/anchors** passed, and `git diff --check` passed. Commit author and committer
must remain the required `ih4c` identity.

M1-02b adds only `core/digests.py`, `core/identities.py`, synthetic vectors/tests
and documentation. Source revisions are independent of transform versions and
parsed metadata; separate immutable association keys prevent bundle overwrites.
No existing model, public protocol, dependency, D027 limit or expected failure
is changed. Validation on Python **3.11.18 and 3.14.10**: **732 passed, one existing
strict TLP xfail** on each. Ruff lint/format and the **15 dependency-boundary tests**
pass. Synthetic vectors cover 11 identity scenarios, five canonical JSON examples
and seven digest domains; helper calls are checked for filesystem/network/clock/
randomness side effects. Documentation links and diff checks accompany the PR.

Follow [HANDOFF.md](HANDOFF.md) and [DECISIONS.md](DECISIONS.md). Recommended next:
**M1-03 SQLite evidence persistence**, after M1-02b review/merge and separate owner
approval. Enforce immutable association keys, transactional references and policy
lifecycle there. Helpers verify supplied values only, not actual backing bytes,
rights, availability, publisher truth or conditional-checkpoint eligibility.
Issue #10 remains open; B1/B2/C are not approved.
