# Proposed modular architecture (not yet finalized)

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

## Proposed initial deployment
GitHub for code and PRs; local/Codex development; GitHub Actions for tests and cautiously scheduled ingestion; SQLite for prototype; GitHub Pages for approved public Markdown output. **Do not use public GitHub artifacts or Actions logs to store restricted intelligence.** Reassess scheduling/storage limits and migrate to a small VPS when needed.

## Contracts
Define versioned `SourceItem`, `EvidenceRecord`, `Indicator`, `Assessment`, `ReviewDecision`, and `Report` models. Preserve source-level identifiers, raw reference links, confidence, TLP markings, and lineage. Never let an adapter directly publish.

## Security and resilience
Untrusted source text cannot issue instructions to agents; least privilege; no secret commits; request timeouts; bounded retries; input validation; no malware execution; human publication gate; structured logs without sensitive payloads.
