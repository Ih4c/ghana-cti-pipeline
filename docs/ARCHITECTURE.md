# Modular architecture and deployment options

The package boundaries and V1 foundation contracts are implemented. Runtime
services, persistence, scheduling and publication remain proposals; consult
[STATUS.md](STATUS.md), [DECISIONS.md](DECISIONS.md), and the approved milestone
specification before implementation. The full pipeline below is the target,
not a statement that every stage currently exists.

```
Source adapters (independent)
    -> scheduler/queue -> normalized evidence store -> triage/ranking
    -> analyst review queue -> analyst-led enrichment & analysis
    -> report drafting/review -> explicit approval gate -> public TLP:CLEAR publishing
```

## Component boundaries
- `collectors/`: adapters implement one common fetch/parse interface; source failures isolated.
- `core/`: schemas, provenance, identifiers, error types, configuration, audit events.
- `triage/`: deterministic filtering and optional LLM-assisted prioritization; no unsourced claims.
- `enrichment/`: deterministic extraction and enrichment utilities, outputs pending analyst validation.
- `analysis/`: analyst-authored assessments and evidence links, not autonomous attribution.
- `reporting/`: Markdown templates, validation, approval, TLP checks, and publication exporter.
- `storage/`: repository interfaces; SQLite may suit local MVP, with later migration path.

## Deployment options and current proposal
GitHub hosts code/PRs and fixture CI. The [M1 plan](milestones/M1_COLLECTION.md)
proposes an approved private host, SQLite retained metadata and optional permitted
raw snapshots, with manual execution first and an optional local timer after
explicit activation. Hosted Actions ingestion is
deferred until private durable storage and operational controls are designed.
GitHub Pages remains an option for later approved public Markdown output; no
publisher or hosting choice is authorized here. **Do not use public GitHub
artifacts or Actions logs to store restricted intelligence.** Reassess scheduling,
storage, backups and costs before selecting or migrating to a small VPS.

## Contracts
The versioned `SourceItem`, `EvidenceRecord`, `Indicator`, `Assessment`,
`ReviewDecision`, and draft-only `Report` models exist; see
[FOUNDATION.md](FOUNDATION.md). Preserve source-level identifiers, raw reference
links, confidence, TLP markings, and lineage. New transport/observation contracts
need reviewed versions and migrations. Never let an adapter directly publish.

The owner's accepted hybrid direction preserves permitted CISA catalog data and
uses metadata-first vendor RSS. Its [technical design](milestones/M1_EVIDENCE.md)
remains proposed: response descriptors do not imply archiving, and additive V2
evidence can omit excerpts without weakening V1. Only approved raw-backed sources
have snapshot artifacts; metadata-only sources use retained projections and
processing manifests. Both preserve provenance while exposing verification limits.
No hybrid contracts or storage are implemented, and later reporting must retain
the existing template and human review requirements.

## Security and resilience
Untrusted source text cannot issue instructions to agents; least privilege; no secret commits; request timeouts; bounded retries; input validation; no malware execution; human publication gate; structured logs without sensitive payloads.
