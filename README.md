# Ghana CTI Pipeline

**Status:** planning / initial scaffold. Public, Ghana-focused cyber threat intelligence platform.

## Purpose
Continuously collect credible cybersecurity information, prioritize Ghana-relevant developments, and support human analysts in creating defensible tactical and operational intelligence with strategic implications where supported.

## Working principles
- Modular, independently maintainable collectors and pipeline components.
- AI assistance in source gathering (partly) and reading/triage, following the original five-stage reference workflow.
- Human-led enrichment, analysis/attribution, and writing; no autonomous publication.
- Evidence provenance, confidence, TLP-aware handling, and explicit human approval.
- Open-source development with protected `main` and PR-based changes.

Start with [Project Vision](docs/PROJECT_VISION.md), [Requirements](docs/REQUIREMENTS.md), [Architecture](docs/ARCHITECTURE.md), and [Roadmap](docs/ROADMAP.md). Codex instructions are in [AGENTS.md](AGENTS.md).

## Milestone 0 development

This scaffold provides typed contracts and module interfaces only. There are no
live collectors, AI calls, storage backends, approval workflows or publishers.
See [Foundation proposal and contracts](docs/FOUNDATION.md) for boundaries,
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
