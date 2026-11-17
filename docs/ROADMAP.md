# Phased roadmap

## Milestone 0 — Documentation and foundation (first Codex PR)
- Review this handover; identify unresolved decisions.
- Propose Python package layout, typed schema contracts, and minimal test strategy.
- Add basic lint/test CI; no live collection or public deployment.
- Demonstrate branch -> PR -> review -> merge workflow.

## Milestone 1 — Minimal source ingestion
- Integrate 2–3 approved, machine-readable sources with separate adapters.
- Normalize records, store provenance, deduplicate, isolate failures.
- Fixture tests and source-specific operational notes.

## Milestone 2 — Ghana-relevance triage
- Create explicit relevance rubric; deterministic baseline first.
- Optional bounded LLM-assisted reading/triage, with source citations and budget controls.
- Human review queue for priority items.

## Milestone 3 — Analyst workflow
- IOC extraction/dedup utilities, verification status, evidence linking.
- Human-led analysis and attribution with confidence and audit trails.
- TLP classifications and restricted-data separation.

## Milestone 4 — Reporting and public MVP
- Adapt permitted Markdown reporting template.
- Analyst review/approval; publish only approved TLP:CLEAR content.
- Public portal and basic search/indexing.

## Milestone 5 — Mature intelligence program
- Additional Ghana/sector sources, operational monitoring, backups, costs.
- Monthly/quarterly summaries and annual Ghana-centric CTI report from verified records.
- Optional authenticated distribution for nonpublic TLP material.

## Approval gates
Each milestone is proposed and reviewed before implementation. No autonomous attribution, no public publishing without explicit human approval, no source ingestion that violates access terms.
