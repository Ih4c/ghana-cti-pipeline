# Documentation guide

Permanent project requirements are separate from milestone scope and current status.
Read in this order when starting or resuming work:

1. [AGENTS.md](../AGENTS.md): permanent engineering, privacy, identity and approval rules.
2. [Vision](PROJECT_VISION.md), [requirements](REQUIREMENTS.md), [five-stage workflow](CTI_WORKFLOW.md) and [reporting standards](REPORTING_STANDARDS.md): what the project serves and the human/AI boundaries.
3. [Architecture](ARCHITECTURE.md) and [foundation contracts](FOUNDATION.md) and [M1 retrieval contracts](M1_RETRIEVAL_CONTRACTS.md) and [full-text evidence contracts](M1_EVIDENCE_CONTRACTS.md) and [identity/digest profiles](M1_IDENTITY_PROFILES.md) and [offline SQLite storage](M1_SQLITE_STORAGE.md) and [recovery/lifecycle](M1_LIFECYCLE.md) and [offline HTTPS transport](M1_TRANSPORT.md): boundaries, implemented interfaces and limitations.
4. [Status](STATUS.md) and [decisions](DECISIONS.md): what exists, what is approved and what is unresolved.
5. [Roadmap](ROADMAP.md), [milestone specifications](milestones/README.md), and the applicable versioned specification/readiness plan: scope, approval boundaries, dependencies and acceptance criteria.
6. [Source register](INTELLIGENCE_SOURCES.md) and [Milestone 1 feasibility evidence](milestones/M1_SOURCE_FEASIBILITY.md) when planning collection.
7. [Handoff](HANDOFF.md): repeatable continuation and review procedure.

Permanent requirements remain binding across milestones. A specification narrows
scope; it cannot silently weaken them. If documents conflict, record and resolve
the conflict before dependent implementation. Current user authorization governs
the task; record its scope without fabricating a decision or approval reference.

Update STATUS for progress, DECISIONS for rationale/approval, and the applicable
specification for scope changes. Keep evidence and approval references in Git;
do not put personal identities, session URLs, secrets, or collected intelligence
in handoffs. The [archive](archive/README.md) preserves historical instructions
and has no authority over current work.
