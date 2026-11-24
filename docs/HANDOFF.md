# Reusable project handoff

This is a procedure/template, not an instruction to implement a particular
milestone. The current milestone and blockers live in [STATUS.md](STATUS.md).

## Resume procedure

1. Read [AGENTS.md](../AGENTS.md) and the [documentation guide](README.md).
2. Verify the remote is `Ih4c/ghana-cti-pipeline`, working-tree changes, latest
   `origin/main`, active branches and related PRs. Preserve unrelated work.
3. Read STATUS, DECISIONS and the applicable milestone specification/version.
   Separate delivered behavior from plans and known expected failures.
4. Confirm explicit approval covers the intended work and specification version;
   verify the author and exact scope of the linked owner comment. The current
   [authorization record](DECISIONS.md)
   and [implementation status](STATUS.md) distinguish approved work from later gates.
   If absent, prepare or revise the plan only. Do not implement collectors, activate sources, incur
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
- Implemented contract versions, compatibility checks and unresolved validation boundaries:
- Source-revision versus derivation/association identity decisions, selected profile
  versions, fixed namespaces/golden vectors and unresolved migrations
  ([current M1 profiles](M1_IDENTITY_PROFILES.md)):
- Checks run and outcomes; expected failures and their reasons:
- Source feasibility evidence and remaining uncertainties:
- Owner-reported observations versus independently verified findings and their dates:
- Rights basis versus risk acknowledgement; superseded scope and fresh approval required:
- Collection representation, policy/retention version, backing availability and verification limits:
- Persistence schema/API versions, immutable association keys, transaction and
  checkpoint integrity checks, tested recovery boundaries and remaining lifecycle
  gates ([offline storage](M1_SQLITE_STORAGE.md), [lifecycle/runbook](M1_LIFECYCLE.md)):
- Trusted rights-ledger authority/deadline, pending maintenance, managed-copy inventory,
  restore isolation and precise logical-versus-physical deletion claims:
- Authoritative report-template reference and any unresolved artifact/license check:
- Decisions accepted/proposed/open (stable IDs):
- Operational state: enabled sources, scheduler, storage, spend, deployments:
- Next authorized action and explicit stopping point:

Never copy source payloads, restricted intelligence, secrets, personal names or
emails, co-author/model lines, or session links into a handoff. Public source
references and repository review links are appropriate evidence. Leave enough
context to continue without relying on this chat's history.
