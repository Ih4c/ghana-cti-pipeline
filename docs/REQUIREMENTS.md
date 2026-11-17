# Requirements (initial, subject to refinement)

## Functional
- Pluggable source adapters for trusted feeds and research publications.
- Scheduled and manually triggered collection with per-source state, retries, rate limiting, and isolation.
- Normalized record schema; content hashes / canonical URLs for deduplication.
- Provenance: exact source URL, publisher, observed/publication dates when known, retrieval time, original excerpt/reference.
- Triage queue prioritizing relevance to Ghana, evidence strength, novelty, urgency, and potential impact. AI-generated explanations must be labeled and source-grounded.
- Analyst review of IOCs, affected products/sectors, TTPs, and any Ghana-specific assertions.
- Approval workflow: draft -> review -> approved/rejected -> published. Track reviewer and timestamps.
- TLP classification and storage separation. No restricted data in public repo or static site.
- Markdown-based report output and future monthly/quarterly/annual aggregation.

## Nonfunctional
- Low-cost prototype, configurable LLM/API budgets, and no hard requirement for paid services.
- Secure secrets, sanitized logs, safe URL handling, and prompt-injection resilience.
- Idempotent jobs, observability, reproducible tests, and graceful partial failure.
- Modular components and source adapters; interfaces documented.
- Public GitHub repo; PR-only changes to protected main.

## Explicit uncertainties to resolve
- Source-by-source legal/ToS access methods and API quotas.
- Storage/hosting choices beyond MVP; backup and retention policy.
- Ghana relevance rubric and minimum evidence standard.
- Restricted sharing workflow and recipient access management.
- Report approval UX and publishing platform.
- Funding, deployment schedule, and maintenance ownership.
