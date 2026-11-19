# Milestone specifications

Each specification has an ID, specification version, lifecycle state, approval
record, scope/non-goals, dependencies, decisions, costs, acceptance criteria, and
handoff requirements. Git versions the document; the version field identifies
the exact scope being approved. Increase it when scope or acceptance changes.

Lifecycle: proposed → approved → in progress → completed; superseded versions
remain in Git history. Approval must identify the version and approved scope,
including any source or operational conditions. A merged planning document alone
does not move a specification to approved. Record approval in
[DECISIONS.md](../DECISIONS.md) and [STATUS.md](../STATUS.md), with a PR review or
other durable repository reference. Approval may cover offline implementation
while leaving live activation blocked; state this explicitly.

| Specification | State | Purpose |
| --- | --- | --- |
| [M0 foundation](M0_FOUNDATION.md), v1.0 retrospective | Completed | Records the delivered foundation and remaining limits |
| [M1 collection](M1_COLLECTION.md), v1.3 | Full-text strategy accepted; technical design proposed, M1-01 unapproved | All three sources, lawful full-text basis, preserved security/operational gates |
| [M1 full-text evidence](M1_EVIDENCE.md), design v1.1 | Proposed; D022 strategy accepted only | Original/sanitized/plain text, V1 compatibility, rights, full-text 304, capacity/deletion and reporting |
| [M1 readiness / PR plan](M1_READINESS.md), review v1.2 | Proposed, awaiting scoped approval | Revised M1-01, small dependent PRs, components, acceptance tests and exclusions |
| [M1 source feasibility](M1_SOURCE_FEASIBILITY.md) | Dated supporting evidence | Separates verified access facts from remaining checks |
| [Template](TEMPLATE.md) | Reusable | Starting point for later milestone specifications |

Milestones 2–5 remain [roadmap](../ROADMAP.md) items until their specifications
are reviewed. Do not create implied implementation approval from their presence.
