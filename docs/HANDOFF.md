# Reusable project handoff

This is a procedure/template, not an instruction to implement a particular
milestone. The current milestone and blockers live in [STATUS.md](STATUS.md).

## Resume procedure

1. Read [AGENTS.md](../AGENTS.md) and the [documentation guide](README.md).
2. Verify the remote is `Ih4c/ghana-cti-pipeline`, working-tree changes, latest
   `origin/main`, active branches and related PRs. Preserve unrelated work.
3. Read STATUS, DECISIONS and the applicable milestone specification/version.
   Separate delivered behavior from plans and known expected failures.
4. Confirm explicit approval covers the intended work. If absent, prepare or
   revise the plan only. Do not implement collectors, activate sources, incur
   costs, deploy or publish merely because a roadmap says they come next.
5. Use a feature branch from verified current main, or the authorized existing
   PR branch. Do not reuse superseded commits or merge your own PR.
6. Before each commit, explicitly set all four author/committer identity
   variables as required by AGENTS. Verify the resulting metadata locally before
   pushing; use only `ih4c` and the specified noreply address.
7. Run applicable checks, update status/decisions/specifications, and prepare a
   concise PR. Documentation work should leave application code and workflows
   unchanged unless separately authorized.

## Handoff record template

Copy the following fields into the task's PR description or a dated status update:

- Date and verified main SHA:
- Feature branch, head SHA and PR:
- Milestone ID, specification version and lifecycle state:
- Approval reference and exact scope; remaining approval gates:
- Changed files and resulting behavior:
- Checks run and outcomes; expected failures and their reasons:
- Source feasibility evidence and remaining uncertainties:
- Decisions accepted/proposed/open (stable IDs):
- Operational state: enabled sources, scheduler, storage, spend, deployments:
- Next authorized action and explicit stopping point:

Never copy source payloads, restricted intelligence, secrets, personal names or
emails, co-author/model lines, or session links into a handoff. Public source
references and repository review links are appropriate evidence. Leave enough
context to continue without relying on this chat's history.
