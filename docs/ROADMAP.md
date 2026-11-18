# Phased roadmap

This is the long-term sequence, not implementation authorization. Current state
lives in [STATUS.md](STATUS.md); scope and acceptance criteria live in
[versioned milestone specifications](milestones/README.md). Approvals and changes
are recorded in [DECISIONS.md](DECISIONS.md).

## Milestone 0 — Documentation and foundation
- Review this handover; identify unresolved decisions.
- Propose Python package layout, typed schema contracts, and minimal test strategy.
- Add basic lint/test CI; no live collection or public deployment.
- Demonstrate branch -> PR -> review -> merge workflow.

Delivered foundation and follow-up review are recorded in the
[M0 retrospective](milestones/M0_FOUNDATION.md), rather than an active first-task instruction.

## Milestone 1 — Minimal source ingestion
- Integrate 2–3 approved, machine-readable sources with separate adapters.
- Normalize records, store provenance, deduplicate, isolate failures.
- Fixture tests and source-specific operational notes.

The [M1 v1.0 collection plan](milestones/M1_COLLECTION.md) proposes the three
named candidates, private storage and operational controls. It remains unapproved.

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
Each milestone is proposed and explicitly approved before implementation.
Documentation merges alone do not approve implementation or source activation.
No autonomous attribution, no public publishing without explicit human approval,
no source ingestion that violates access terms, and no self-merging PRs.
