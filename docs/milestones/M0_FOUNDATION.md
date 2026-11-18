# M0 — Foundation (retrospective)

- Specification version: 1.0 retrospective, recorded 2026-11-18
- State: completed
- Original task: [archived handover](../archive/CODEX_FIRST_TASK.md)
- Delivery evidence: [PR #2](https://github.com/Ih4c/ghana-cti-pipeline/pull/2), merged as `8ef86de`, and [PR #3](https://github.com/Ih4c/ghana-cti-pipeline/pull/3), merged as `8d3dff3`
- Approval record: those merged deliveries establish accepted foundation work; they do not approve later milestones.

Delivered a modular Python package, six versioned domain contracts, collector and
storage protocols, synthetic fixture tests, locked dependencies and lint/test CI.
Follow-up review added package-root/dynamic-import boundary checks, validated
copies, proposed size limits and a strict expected-failure TLP inheritance test.
Permanent commit identity rules require `ih4c` and the specified noreply address.

Acceptance evidence: the merged code has 73 passing tests and one deliberate
xfail; CI covers Python 3.11 and 3.14. This documentation PR rechecks the baseline.
The xfail records missing TLP inheritance, not a working authorization control.

No live adapter, scheduler, database backend, AI calls, analyst application,
authenticated approval workflow, deployment or publisher was delivered. These
limits and the current contracts are documented in [FOUNDATION.md](../FOUNDATION.md).
F5 validation hardening, F6 static typing, and F7 fetch-time SSRF protection were
not implemented by the foundation review; see [STATUS.md](../STATUS.md).
