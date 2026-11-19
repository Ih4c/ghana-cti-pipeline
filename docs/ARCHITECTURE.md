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
proposes an approved private host, SQLite permitted full-text originals and derived
artifacts, with manual execution first and an optional local timer after
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
links, confidence, TLP markings, and lineage. The additive [retrieval/observation contracts](M1_RETRIEVAL_CONTRACTS.md)
have their own versions; breaking changes require reviewed versions and migrations. Never let an adapter directly publish.

The owner's accepted v1.3 direction (D022) targets complete permitted CISA catalog
entries and vendor feed-supplied full articles. The [technical design](milestones/M1_EVIDENCE.md)
is proposed: keep complete response, original article field, sanitized HTML and
plain text distinct, with independent hashes/versions/lineage and explicit backing
availability. Authorized originals and derivatives stay in private storage; raw
bodies never belong in public Git, CI or logs. Full-text rights unresolved means
activation blocked, not metadata substitution. V1 shapes/excerpt rules remain
unchanged. M1-01 descriptors are delivered by PR #8. Additive [M1-02a evidence
contracts](M1_EVIDENCE_CONTRACTS.md) had separate approval and are delivered by PR #9; all runtime/processing work remains unapproved.
The existing report template and human review requirements remain authoritative.

## Security and resilience
Untrusted source text cannot issue instructions to agents; least privilege; no secret commits; request timeouts; bounded retries; input validation; no malware execution; human publication gate; structured logs without sensitive payloads.
