# Copy into a new Codex task after the handover files are in the repository

Read `AGENTS.md` and every document in `docs/` before making changes. Treat them as the project requirements. This is a public, Ghana-focused, modular CTI platform; it is not a DNS-only or Microsoft-only project.

Your first task is **Milestone 0 only**: assess the proposed architecture, identify unresolved decisions, and scaffold the smallest Python project structure, typed domain models/interfaces, fixture-based tests, and GitHub Actions lint/test checks. Keep components independently replaceable. Do not ingest live sources, call paid APIs, create a public deployment, or publish intelligence yet. Do not introduce autonomous AI enrichment, attribution, or reporting: the reference workflow has AI assisting Stage 1 partly and Stage 2, while Stages 3–5 are human-led. Preserve human review and TLP controls.

Work on a feature branch, make a small reviewable PR against protected `main`, and report what was tested, what remains undecided, and expected costs. Do not merge your own PR or bypass protections.
