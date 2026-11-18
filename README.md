# Ghana CTI Pipeline

Public, Ghana-focused cyber threat intelligence platform. See [project status](docs/STATUS.md) for delivered capabilities, the active proposal, and approval gates.

## Purpose
Continuously collect credible cybersecurity information, prioritize Ghana-relevant developments, and support human analysts in creating defensible tactical and operational intelligence with strategic implications where supported.

## Working principles
- Modular, independently maintainable collectors and pipeline components.
- AI assistance in source gathering (partly) and reading/triage, following the original five-stage reference workflow.
- Human-led enrichment, analysis/attribution, and writing; no autonomous publication.
- Evidence provenance, confidence, TLP-aware handling, and explicit human approval.
- Open-source development with protected `main` and PR-based changes.

Start with the [documentation index](docs/README.md). Permanent development rules are in [AGENTS.md](AGENTS.md); scope and approval belong in the [milestone specifications](docs/milestones/README.md), [decision log](docs/DECISIONS.md), and [project status](docs/STATUS.md). Use the [handoff guide](docs/HANDOFF.md) to continue work.

## Development

This scaffold provides typed contracts and module interfaces only. There are no
live collectors, AI calls, storage backends, approval workflows or publishers.
See [Foundation contracts](docs/FOUNDATION.md) for boundaries,
failure semantics, unresolved decisions, expected costs and the phased plan.

With Python 3.11+ and [uv](https://docs.astral.sh/uv/) 0.13.6 installed:

```sh
uv sync --locked
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen pytest
```

Dependency installation needs package-index access; tests use synthetic fixtures
and block socket connections. Keep real collected evidence out of this public
repository. Submit changes on feature branches through PR review.
