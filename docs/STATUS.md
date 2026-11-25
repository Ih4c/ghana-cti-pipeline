# Project status

Last reviewed: **2026-11-25**. Repository: `Ih4c/ghana-cti-pipeline`.
Application contracts delivered by [PR #9](https://github.com/Ih4c/ghana-cti-pipeline/pull/9) (M1-02a),
with D027 numeric caps delivered by [PR #15](https://github.com/Ih4c/ghana-cti-pipeline/pull/15);
documentation follow-ups [PR #12](https://github.com/Ih4c/ghana-cti-pipeline/pull/12)
and [PR #13](https://github.com/Ih4c/ghana-cti-pipeline/pull/13), and the RSS investigation
[PR #14](https://github.com/Ih4c/ghana-cti-pipeline/pull/14), are merged.
M1-02b helpers are delivered by [PR #16](https://github.com/Ih4c/ghana-cti-pipeline/pull/16).
M1-03 offline persistence is delivered by [PR #17](https://github.com/Ih4c/ghana-cti-pipeline/pull/17).
M1-04 offline lifecycle is delivered by [PR #18](https://github.com/Ih4c/ghana-cti-pipeline/pull/18).
M1-05 offline transport is delivered by [PR #19](https://github.com/Ih4c/ghana-cti-pipeline/pull/19).
M1-06a pure source parsing is delivered by [PR #20](https://github.com/Ih4c/ghana-cti-pipeline/pull/20).
Verified against GitHub on 2026-11-25: main was `64224f1` (the PR #20 merge). This
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
| M1 v1.3 technical design | PR #7 merged; **M1-01 through M1-06b scoped offline work approved**, remaining design proposed | [Specification](milestones/M1_COLLECTION.md), [full-text evidence/rights design](milestones/M1_EVIDENCE.md), [PR sequence](milestones/M1_READINESS.md) |
| M1-01 implementation | Delivered by PR #8 | Five [retrieval/observation contracts](M1_RETRIEVAL_CONTRACTS.md), discriminated outcomes, synthetic fixtures/tests; no I/O |
| M1-02a implementation | Delivered by [PR #9](https://github.com/Ih4c/ghana-cti-pipeline/pull/9) | [V2 evidence, artifact, policy and manifest contracts](M1_EVIDENCE_CONTRACTS.md); synthetic tests only |
| Documentation consistency | PR #12 and PR #13 merged; Issue #11 closed | Current-state sync and permanent pre-PR SHA/PR-state/test-count checks delivered; historical milestone references preserved |
| RSS size investigation | Delivered by PR #14; Issue #10 open | [Limits, B1 measurement plan and decision matrix](milestones/M1_RSS_SIZE_INVESTIGATION.md); actual sizes/headroom unmeasured |
| D027 numeric-cap amendment | Delivered by PR #15 | RSS response and each representation aggregate 6 MiB, article fields 1 MiB; synthetic boundary tests only; no B1/B2/C approval |
| M1-02b identities/digests | Delivered by PR #16 | [Profiles, namespaces and D026 resolution](M1_IDENTITY_PROFILES.md), pure helpers, synthetic vectors and supplied-record checks; no I/O |
| M1-03 SQLite persistence | Delivered by PR #17 | [Offline storage reference](M1_SQLITE_STORAGE.md); atomic synthetic batches, immutable associations, replay/rollback, policy-bound bytes and validated 304 checkpoints; no operational activation |
| M1-04 recovery/lifecycle | Delivered by PR #18 | [Offline lifecycle/runbook](M1_LIFECYCLE.md); bounded private workspace, consistent backup, isolated restore, rights ledger and policy purge; no production job |
| M1-05 HTTPS transport | Delivered by PR #19 | [Transport profiles and limits](M1_TRANSPORT.md); injected-fake DNS/TLS/HTTP/clock tests, safe descriptors and caller-owned budgets; no source endpoints or live I/O |
| M1-06a source parsing | Delivered by PR #20 | [Pure parsing profile](M1_PARSING.md); Expat RSS 2.0/JSON with synthetic fixtures, bounded complete fields and safe failures; no source mapping or HTML transformation |
| M1-06b HTML/text transformations | Approved; implemented on this feature branch for independent review | [Strict inert transformation profile](M1_TRANSFORMS.md); separately versioned helpers, preserved originals and bounded all-or-nothing synthetic batches; no integration or live content |
| M2–M5 | Roadmap only | No implementation or publication approval |

Main delivers the foundation, M1-01 through M1-06a and D027 (1,112 passed, one
existing strict TLP xfail). This branch adds pure offline HTML/text transformations.
No source adapters, orchestration, scheduler or publisher exists.
The unfinished v1.2 draft remains preserved in its original worktree.

## Blockers and decisions

1. **M1-06b offline HTML/text transformations approved.** The
   [owner comment on PR #20](https://github.com/Ih4c/ghana-cti-pipeline/pull/20#issuecomment-7149971631)
   approves D024 pure standard-library sanitization and extraction of already
   extracted article strings, separate versions, bounded deterministic output,
   unchanged originals, synthetic adversarial tests and documentation. Author/scope
   were verified before application changes. [D032](M1_TRANSFORMS.md) records the
   narrow fragment grammar, allowlist, escaping, text separators and budgets for
   review. No dependency was added. M1-07 onward and B1/B2/C need fresh approval.
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
4. **Technical choices remain scoped.** D005/D013/D019 offline persistence is now
   delivered by PR #17 with D028 schema/API bindings. M1-04 offline mechanisms are
   delivered by PR #18 with D029. M1-05 transport/D030 is delivered by PR #19.
   M1-06a parsing/D031 is delivered by PR #20. M1-06b has separate approval; D032
   records its concrete profile for review. Source mappings, integration, real-host
   transport/capacity verification and operational jobs need their respective approvals.
   D018 collection strategy superseded; D009/D021 remain open. D025 wire bindings
   are delivered by PR #9; D026 source-revision versus derivation identity
   is resolved in the [profile specification](M1_IDENTITY_PROFILES.md). Review
   its exact projections and association keys when composing future adapters.
   Real-host controls and operational lifecycle jobs remain unimplemented.
5. **Capacity and operations unresolved.** Keep 2 GiB live cap and $0 paid-service
   budget. Up to 64 MiB/day before overhead cannot fit annual retention. Explicitly
   decide lawful retention/capacity after approved measurements; never increase
   storage silently. Private host/operator, encryption/keys, real-host backup/WAL/purge behavior,
   one-cycle/24h budgets and publisher-stricter restrictions require verification.
   Offline tests do not prove physical erasure or independently establish rights.
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
interfaces; M1-02a validates declared full-text byte/count bounds; M1-05 transport and M1-06a
parsers enforce their actual input/field bounds in offline tests. Source integration
remains future work. F4 strict TLP xfail blocks export.
F5-wide V1 hardening/F6 tooling remain separate. F7 contract URL syntax alone is
not SSRF defense; M1-05 adds separately tested transport controls. Runtime/source
verification remains gated.

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

PR #16 delivered only `core/digests.py`, `core/identities.py`, synthetic vectors/tests
and documentation. Source revisions are independent of transform versions and
parsed metadata; separate immutable association keys prevent bundle overwrites.
No existing model, public protocol, dependency, D027 limit or expected failure
is changed. Validation on Python **3.11.18 and 3.14.10**: **732 passed, one existing
strict TLP xfail** on each. Ruff lint/format and the **15 dependency-boundary tests**
pass. Synthetic vectors cover 11 identity scenarios, five canonical JSON examples
and seven digest domains; helper calls are checked for filesystem/network/clock/
randomness side effects. Documentation links and diff checks accompany the PR.

PR #17 delivered four storage modules, a synthetic fixture builder and focused temporary
database tests. All existing core contracts, helpers, protocols, dependencies,
CI configuration, numeric caps and report template remain unchanged. New tests
cover reopen, replay, A→B→A/transform history, FK/conflict failures, transaction
rollback, policy/retention gates, damaged backing and 304 chains. Full-suite
validation on Python **3.11 and 3.14**: **811 passed, one existing strict TLP xfail**
on each; **79** tests exercise the new store. Ruff lint/format, **15 dependency-boundary tests**, **183 local Markdown
links/anchors** and diff checks pass. No live source requests or
operational actions occurred.

PR #18 delivered five storage modules, one focused synthetic test module and a lifecycle
reference/runbook. Existing M1-03/core code, wire contracts, schema v1, dependencies,
CI and report template remain unchanged. Verification covers all retained graphs,
not only the newest checkpoint. Purge preserves shared bytes only through surviving
independent policy associations. Restore candidates have no operational selectors.
New tests cover real child-process crash rollback, WAL recovery, SQLite FULL and
read-only errors, locks, corruption, backup permissions/deadlines, ledger integrity,
interrupted purge/backup, policy retirement and absence of synthetic canaries from
remaining managed files. A purge result never claims physical erasure.

Validation: **852 passed, one existing strict TLP xfail** on Python **3.11 and
3.14**; **41** new lifecycle cases. Ruff lint/format, **15 dependency-boundary
tests**, **192 local Markdown links/anchors** and diff checks pass. No source requests or operational jobs occurred.

PR #19 delivered five collector-side transport modules, a synthetic fake harness and
focused tests, plus D030 and a transport reference. Existing core/storage code,
protocols, wire versions, dependencies, CI and report template remain unchanged.
The transport returns complete 200/304 or safe failure descriptors; bounded 200
body bytes are separate and transient, with no retention or source-activation
claim. No real host was contacted or resolved.

Validation: **981 passed, one existing strict TLP xfail** on Python **3.11 and
3.14**; **129** transport cases. Ruff lint/format, **15 dependency-boundary tests**,
**200 local Markdown links/anchors** and diff checks pass. Tests verify exact/over-limit headers and bodies, decompression
bombs, peer/SNI/IP binding, rebinding, redirects, deadlines, budgets, conditionals,
403 behavior, Retry-After and source isolation with all real network calls blocked.

PR #20 delivered three pure collector-side parser/value modules, a synthetic fixture
builder and focused tests, plus D031 and a parsing reference. Existing core,
transport/storage, wire contracts, interfaces, digest profiles, dependencies,
CI and report template remain unchanged. Standard-library Expat and JSON preserve
complete supplied fields with no fallback, original-byte/decoded-field confusion,
source mappings, inferred dates or analytical claims. No real source was contacted.

Validation: **1,112 passed, one existing strict TLP xfail** on Python **3.11 and
3.14**; **131** parser cases. Ruff lint/format, **15 dependency-boundary tests**,
**217 local Markdown links/anchors** across **31 documents**, and diff checks pass.
Side-effect traps and static import checks cover filesystem/network/clock/randomness
exclusions. Exact/one-over tests cover input/body/metadata/depth/count limits;
existing suites preserve V1 through M1-05 compatibility.

M1-06b adds five collector-side modules for a shared strict HTML fragment profile,
independent sanitizer/extractor and atomic in-memory batch helper, plus one synthetic
test module and D032/reference documentation. Original input is preserved separately
from the inert attribute-free HTML and plain-text derivatives. Existing core,
transport/storage/parsers, contracts, profiles, interfaces, dependencies, CI and
report template remain unchanged. No real source content or I/O is involved.

Validation: **1,247 passed, one existing strict TLP xfail** on Python **3.11 and
3.14**; **135** transformation cases. Ruff lint/format, **15 dependency-boundary
tests**, **234 local Markdown links/anchors** across **32 documents**, and diff
checks pass. Synthetic vectors/adversarial cases cover inert output, strict syntax,
entity handling, original preservation and exact caps; side-effect traps/static
imports confirm no filesystem/network/clock/randomness use.

Follow [HANDOFF.md](HANDOFF.md) and [DECISIONS.md](DECISIONS.md). Stop at independent
M1-06b review. Review D032's strict grammar, allowlist, node/attribute accounting,
separator rules and runtime compatibility. This intentionally rejects some
browser-recoverable HTML; source compatibility needs future B1 evidence. Inert
output is not viewer certification, completeness verification or publication
permission. Next proposed increment: **M1-07 offline CISA adapter**, after separate
scoped approval. Lawful basis remains open and blocks real full-text activation.
Source mappings, host/capacity checks and operational integration remain gated;
Issue #10 stays open and B1/B2/C are not approved.
