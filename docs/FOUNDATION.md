# Foundation contracts and component boundaries

This document describes the implemented foundation and its limitations across
milestones. Current progress and authorized scope live in [STATUS.md](STATUS.md)
and the [milestone specifications](milestones/README.md). Historical delivery is
recorded in the [M0 retrospective](milestones/M0_FOUNDATION.md); the original
[first task](archive/CODEX_FIRST_TASK.md) is archived, not active guidance.
All committed examples are synthetic, using reserved `example.org` references.
No source feasibility or redistribution permission is implied by these contracts.

## Architecture assessment

The proposed adapter → evidence → triage → analyst → reporting separation fits
the vision: tactical and operational intelligence for all Ghanaian organizations,
with strategic conclusions only when supported by verified evidence. A global
advisory alone is not evidence of Ghanaian targeting.

A single Python distribution with separate packages is sufficient for this
stage. Independently replaceable modules do not yet require separate services,
queues, deployments, or databases. Python 3.11+ and Pydantic 2 provide typed,
validated JSON contracts; pytest and Ruff provide offline tests and linting.
These tools are open source. `uv.lock` pins the dependency graph. Pydantic/uv and
the initial V1 shapes were delivered in the merged foundation PRs. Future
contract changes still need explicit review/versioning; see D001 in the decision log.

| Package | Responsibility now | Later boundary |
| --- | --- | --- |
| `core` | Immutable, versioned contracts and vocabulary | Shared schemas, identifiers, configuration, audit events |
| `collectors` | Fetch/parse protocol, source-local error type, offline-testable HTTPS transport and pure RSS/JSON parsers plus HTML/text transformations | Independent permitted-source adapters, Stage 1 (partly AI-assisted) |
| `storage` | V1 repository protocol; additive offline V2 SQLite transactions, immutable associations and policy-bound backing checks | Production lifecycle/host controls and V1 backend |
| `triage` | Package placeholder | Stage 2 deterministic ranking; optional bounded, labeled AI assistance |
| `enrichment` | Package placeholder | Stage 3 deterministic tools, analyst verification, no AI |
| `analysis` | Package placeholder | Stage 4 human judgments and attribution, no AI |
| `reporting` | Package placeholder | Stage 5 human writing, review and explicit publication approval, no AI |

Components import shared `core` contracts rather than each other's concrete
implementations. `core` has no knowledge of downstream packages. A dependency
boundary test checks direct and package-root imports and disallows calls to
`importlib.import_module`, including imported aliases and computed targets, so
dependencies remain statically visible. This AST check is not a security sandbox.
Future orchestration should compose interfaces
outside these packages; it is not implemented now.

## V1 data contracts

All records have `schema_version: "1.0"`, reject extra fields and unsupported
versions, and are frozen after validated construction. IDs are caller-supplied
UUIDs; V1 does not automatically derive source identities. Additive M1-02b
[identity helpers](M1_IDENTITY_PROFILES.md) leave these V1 shapes unchanged. Use
`model_validate`/`model_validate_json` at trust boundaries and `model_dump_json`
for serialization. `Contract.model_copy(update=...)` reconstructs and validates
the resulting record, including updates; nested records may be reconstructed
even for shallow copies. Pydantic's unchecked `model_construct` is not an
ingestion API. Breaking changes need a new schema version and an
explicit migration, never a silent reinterpretation of old evidence.

The proposed [full-text M1 extension](milestones/M1_EVIDENCE.md) does not change
these V1 rules or force complete articles into V1 excerpts. Additive V2
associates permitted original source content and sanitized/plain-text references.
The approved [M1-02a data contracts](M1_EVIDENCE_CONTRACTS.md) were delivered by PR #9;
PR #16 delivers pure digest/identity helpers. Separately approved
[M1-03 storage](M1_SQLITE_STORAGE.md) adds offline persistence for these contracts;
[M1-04 lifecycle mechanisms](M1_LIFECYCLE.md) add offline recovery/capacity and
backup/restore/purge. V1 backend implementation and production operations remain
future work.
The additive [M1-01 descriptors](M1_RETRIEVAL_CONTRACTS.md) are delivered by PR #8.
Response hashes do not imply archived or lawful content.

| Contract | Meaning and preserved information |
| --- | --- |
| `SourceItem` | Exact untrusted excerpt, title, source ID, publisher, original URL, optional canonical URL and source-native ID, optional publication/observation dates, required retrieval time, source TLP |
| `EvidenceRecord` | Immutable source snapshot, SHA-256 of the exact excerpt's UTF-8 bytes, parent evidence IDs and confidence |
| `Indicator` | Inert candidate value/type with evidence links, observation date, confidence and TLP; always pending validation |
| `Assessment` | Human author/time/revision, evidence links, separate facts/hypotheses/unknowns, Ghana relevance and rationale, confidence and TLP |
| `ReviewDecision` | Decision ID, human reviewer/time, rationale and exact subject ID/revision; an append-only audit record intent |
| `Report` | Human author/time/revision, evidence and assessment links, Markdown draft and TLP; draft is the only supported state |

Dates must have a timezone; missing original publication/observation dates remain
null, never replaced with retrieval time. Original URLs are retained exactly,
separate from optional canonical references. URL syntax checks allow HTTP(S)
and reject embedded credentials; they do not establish that a URL is safe to
fetch. Source text and indicator values are inert data, including instructions
embedded in articles. No URL is visited or instruction executed by these models.

The excerpt hash detects changes to the stored excerpt, not publisher authenticity
or integrity of a full original document. Raw response archiving, content hashes
for deduplication, canonicalization, and retention remain Milestone 1 decisions.
Parent IDs preserve lineage links; persistence must later check referential
integrity. Confidence defaults to unknown and is not a computed credibility score.

Ghana relevance defaults to `unknown`. `possible_exposure` and
`confirmed_targeting` are distinct; either requires an analyst rationale and
evidence links. Schema validation cannot verify the truth or sufficiency of a
claim. The evidence threshold and relevance rubric require owner approval.

TLP values match the five TLP 2.0 markings, including `TLP:AMBER+STRICT`.
Null means unclassified, never TLP:CLEAR. These fields are metadata, not access
controls. No source or downstream record is automatically downgraded. Before
implementing enforcement, review official FIRST guidance as required by
`REPORTING_STANDARDS.md` and decide inheritance and mixed-source restrictions.
No restricted real intelligence belongs in fixtures, logs, Actions artifacts or
this public repository. Human actor fields are declarations, not authentication.
Review decisions do not mutate reports or authorize an exporter. Even a
TLP:CLEAR draft with an approval decision cannot be published by this scaffold.
The eventual approval gate must verify identity, evidence/TLP inheritance and
the exact reviewed revision; no such workflow or exporter exists here.

## Interfaces and failure semantics

`Collector.fetch()` is intended to return one bounded `FetchedDocument` containing provenance,
raw bytes and media type. `parse(document)` returns a tuple of normalized
`SourceItem` records without I/O. Multi-page fetching/checkpoints can extend a
future contract after source selection. Adapters must preserve source attribution
and report source-local failures via `CollectorError` (source ID, safe code,
retryability). Its exception message contains no source payload.

**Open Milestone 1 decision — input size limits (F3):** no maximum is currently
enforced for `Text` fields or `FetchedDocument.body`; “bounded” is an adapter
requirement, not a guarantee of this scaffold. Before live ingestion, approve
per-field character limits (identifiers, URLs, titles, excerpts, rationales and
report bodies) and byte limits for fetched bodies, including decompressed data.
The current [M1 specification](milestones/M1_COLLECTION.md) proposes text caps
and source-specific body caps (8 MiB KEV, 6 MiB RSS under D027), superseding earlier 2 MiB
RSS limits. Source feasibility must confirm these before activation. Report
body limits remain a later reporting decision. Enforce body limits while
streaming and after decompression, reject oversized input without silent
truncation, and test at/above each limit before any collector is enabled.

`EvidenceRepository.get(id)` returns a record or None. `add(record)` must be
idempotent for identical ID/content and reject conflicting content with
`ValueError`; a backend must preserve the full snapshot and segregate restricted
or unclassified records. No V1 backend or application access control is provided.
The additive M1-03 store has a separate V2 API and is not a V1 protocol adapter.

Before live collection, each adapter needs explicit timeouts, size limits,
rate limits/Retry-After handling, bounded backoff, permissions and quotas. A future
orchestrator must isolate each source's failure, including unexpected parser
errors, and continue other collectors. Do not retry invalid payloads indefinitely.
Only safe error codes and operational counters should reach public logs; never
log source payloads, credential-bearing URLs, or secrets. Failure isolation and
retry behavior are requirements for Milestone 1, not claims about this scaffold.

## Tests and CI

`tests/fixtures/contracts.json` contains fabricated, explicitly labeled records.
Tests exercise JSON round trips, exact provenance, missing dates, timezone
validation, evidence digests, required evidence links, immutable snapshots,
TLP vocabulary, unknown defaults, Ghana claim rationales, human actor types,
revision-bound reviews, draft-only reports, and dependency direction. A fixture
adapter demonstrates the protocol without networking. Socket connections are
blocked during pytest to detect accidental live-source dependencies.

GitHub Actions runs lint, formatting and tests on PRs and main updates, with
read-only permissions, no persisted checkout credentials, no schedule, no
deployment, and no intelligence artifacts. Python 3.11 and 3.14 cover the
minimum and current stable versions. Actions and dependency versions are pinned;
updates should be reviewed in future PRs. Maintainers should require the CI
checks through branch protection; changing repository settings requires explicit authorization.

## Open decisions and future scope

**Open decision — TLP inheritance (F4), required before any exporter:** a derived
record must not be less restrictive than its sources. A TLP:CLEAR report citing
TLP:RED evidence must be rejected; standalone schemas currently cannot enforce
this because they do not resolve evidence IDs. Decide where evidence resolution
and inheritance checks run, how mixed-source recipient restrictions combine, and
how missing/unclassified evidence fails closed. Review official FIRST guidance
before implementing these rules. The strict xfail test
`test_clear_report_cannot_cite_red_evidence` records the intended rejection using
a proposed evidence lookup context; it is not implemented enforcement or an
approved validation API. Resolve this expected failure before adding an exporter.

Use [DECISIONS.md](DECISIONS.md) for the current decisions, [ROADMAP.md](ROADMAP.md)
for the long-term sequence, and [milestone specifications](milestones/README.md)
for approval scopes and acceptance criteria. Source permissions, stable identity,
private storage, retries, retention, scheduling and operator ownership require
review before collection. Ghana relevance criteria, any bounded/labeled LLM use,
authenticated analyst review, restricted access, report-template licensing,
public hosting and annual aggregation remain later approved work.

The foundation enables no paid service or recurring workload. Local software
has no license fees; public standard-runner CI is expected to remain free under
GitHub's terms. Each milestone must state its own runtime/storage/backup cost
assumptions and approved budget before activation. See the M1 cost proposal;
do not infer that later operations are costless or authorized.
