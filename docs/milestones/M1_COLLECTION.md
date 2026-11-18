# M1 — Minimal intelligence collection plan

- Specification version: **1.0**
- State: **proposed — collector implementation is not approved**
- Updated: 2026-11-18
- Planning baseline: main `8d3dff3cea24b7b9007cf2f5824824da773bcc85`
- Approval: pending owner review; record exact version/scope in [DECISIONS.md](../DECISIONS.md).
- Supporting evidence: [source feasibility, 2026-11-18](M1_SOURCE_FEASIBILITY.md).

## Outcome, scope and approval gates

Collect source-attributed evidence from three independently replaceable candidate
adapters: CISA KEV JSON, Microsoft Security Blog RSS, and the official Google
Threat Intelligence/Mandiant RSS feed. Store normalized records and retrieval
evidence privately, deduplicate repeat observations, retain revisions, and let
one source fail without losing others. These sources support vulnerability and
research coverage for Ghanaian defenders; they are not proof of local targeting.

This PR contains documentation only. **Gate A:** owner approves this version's
implementation scope before any collector, backend, orchestration or related
code is written. **Gate B:** before any live run, each source must pass the
rights/runtime checks in the feasibility document and the operator must approve
the host/storage configuration. **Gate C:** recurring scheduling needs explicit
activation after a successful manual run. None of these approvals is recorded.
The owner can approve offline implementation while retaining B/C as blockers.

Exclude full article scraping, historical vendor backfills, paid APIs, new source
substitution, triage/ranking, LLM calls, IOC extraction, attribution, analyst UX,
report generation, deployment and publication. Later stages remain human-led.
No automatic email/Slack messages, website exports, or blocking actions.

## Source decisions and mapping

| Source ID | Proposed fetch / native identity | Normalization and limitations |
| --- | --- | --- |
| `cisa-kev` | Official CISA mirror JSON in the feasibility register; CVE ID | One item per catalog entry. Title from vulnerabilityName, exact excerpt from shortDescription. Keep the complete entry and catalog metadata in the raw snapshot, identified by JSON pointer and CVE. `published_at` stays null unless a genuine item publication timestamp is supplied; preserve dateAdded/dueDate as dates in source metadata. |
| `microsoft-security-blog` | Registered RSS URL; GUID, otherwise original entry URL | Preserve feed title, link, date and permitted exact summary. Store original publication text and parsed timezone when supplied; malformed dates are flagged, not guessed. GUID stability and description availability need payload verification. |
| `google-threat-intelligence` | Publisher-linked FeedBurner RSS; GUID, otherwise original entry URL | Same feed mapping, with distinct feed/final/article URLs and source attribution. Do not use the premium intelligence API. Validate any claimed original-link extension before using it. |

All source entries retain configured source ID, publisher, original URL,
source-native ID, original date/precision when available, UTC retrieval time,
adapter/parser version and evidence linkage. Missing publication dates remain
unknown. CISA's catalog date is not copied onto every CVE as publication time.
Public availability and CC0 do not automatically set TLP:CLEAR; retain supplied
TLP if present, otherwise null and private handling. Confidence stays unknown;
no Ghana relevance claim is produced by collection.

Vendor summary retention is conditional on rights clearance. No full `content:encoded`
archive is proposed by default. If retaining a raw RSS body would exceed approved
rights, disable the source until a reviewed metadata-only design can preserve
honest provenance. Never silently truncate/rewrite evidence to satisfy a field.

## Architecture and contract evolution

Keep one Python distribution. The existing core contracts and protocol boundaries
remain the starting point; do not make adapters import concrete storage or each
other. Proposed composition:

```text
manual CLI / optional local timer
  -> explicit static adapter registry and per-source runner
  -> bounded HTTPS transport -> independent fetch/parse adapter
  -> normalization + revision identity -> storage interfaces
  -> private SQLite metadata + permitted content-addressed snapshots
```

| Component | Proposed responsibility / test boundary |
| --- | --- |
| `core/` | Existing V1 domain contracts; new versioned retrieval/observation contracts, identifiers, limits and safe error codes. No network/database dependencies. |
| `collectors/` | Separate CISA, Microsoft and Google adapters using fetch/parse separation. Shared injected HTTPS transport and RSS parser may remove duplication; source mapping/permissions remain separate. Parse functions never perform I/O. |
| `storage/` | Implement EvidenceRepository and new retrieval/state repository protocols with SQLite. Enforce immutable ID/content semantics and preserve source-local revisions. |
| New `orchestration/` and CLI | Compose explicit adapters, transport and repositories, isolate failures, apply per-source budgets/checkpoints and return a run summary. This is a documented composition-layer exception to the current component dependency test, to be narrowly tested in the approved implementation. |
| Later-stage packages | No change to triage, enrichment, analysis or reporting behavior. |

Use standard-library SQLite/UUID/hash tools, existing Pydantic contracts, a small
maintained open-source HTTP client with streaming/timeouts, and a hardened XML
parser (for example defusedxml). Pin and review any additions in uv.lock. HTTP
client selection must demonstrate the SSRF controls below; a client library alone
does not supply them. Avoid a broker, microservices, browser automation or dynamic
plugin imports at this scale.

`FetchedDocument` currently lacks status/headers/final URL and conditional-fetch
outcomes. Propose an explicit versioned retrieval result with success/not-modified/
failure variants, transport metadata and snapshot reference; keep `parse` pure.
Add a retrieval record linking configured URL, actual final URL, redirect chain,
UTC retrieval time, status, permitted cache headers, body digest and parser version
to each evidence record and its locator. Do not put operational state or mutable
last-seen fields into immutable evidence. Review contract changes/migration before
implementing them; breaking V1 changes require a new version, never silently
changing `schema_version: 1.0`. No contract changes are made in this plan.

Stable identity: use a fixed, documented UUIDv5 namespace and `(source_id,
source_native_id)` as logical item key; use the exact original URL only as a
fallback where GUID is absent. Revision identity combines that key with a digest
of defined source fields, excluding retrieval time. Separate namespaces identify
source-item snapshots and evidence records. Preserve the hash algorithm/version
and test field ordering/canonical serialization. Exact excerpt SHA-256 retains
its existing narrow meaning; add full response SHA-256 in the retrieval ledger.

Repeated unchanged fetches add observations, not duplicate evidence. Changed
source content creates a new immutable revision linked to its predecessor.
Keep one source's evidence distinct from another's even when URLs or CVEs match.
Canonicalization never overwrites the original reference. Do not drop arbitrary
query strings or treat fetched links as network targets. CISA entries absent from
a later snapshot are marked no-longer-present, not deleted; a rolling RSS window
does not imply retraction. No cross-source claim deduplication in M1.

## Private persistence, retention and recovery

Propose one SQLite database with foreign keys and transactions plus a private
content-addressed directory for permitted response bytes. Logical tables cover
retrievals, immutable evidence revisions, per-item observations, source state,
runs and safe error events. Index source/native identity and revision digest;
enforce same-ID/same-content no-op and same-ID/different-content rejection.
File paths derive only from digests, never from untrusted titles or URLs.

Use a dedicated least-privilege account, owner-only files/directories and encrypted
host storage. SQLite is not encrypted by default. Store outside the checkout,
public web roots, synced public folders and Actions artifacts/caches. M1 accepts
only approved public endpoints; if restricted markings unexpectedly appear,
stop/quarantine privately for review, never downgrade them or export the payload.

Write snapshots atomically, then commit evidence/observations and the successful
checkpoint transactionally. Do not advance ETag/Last-Modified until processing
commits. If disk is full or a transaction fails, keep the previous checkpoint;
restart must retry without losing or duplicating evidence. Reconcile orphaned
snapshot files safely after interrupted writes. Allow only one active writer/run.

Proposed retention: unreferenced raw responses 30 days; evidence, referenced
snapshots and audit/observation metadata at least 365 days, subject to source
permissions. This is a proposed annual-reporting baseline, not permission to
retain copyrighted data indefinitely. If rights cannot support it, defer the
source or approve revised retention/coverage before activation. Record any
approved deletion with hash, date, reason and provenance tombstone. Never silently
break cited evidence links. Later annual aggregation/longer archival is separate.

Reserve a 2 GiB live-store cap and a 512 MiB/day transfer cap; warn at 80%, stop
new collection at capacity, and do not auto-purge cited evidence or buy storage.
Daily encrypted backups to an approved private location (seven daily restore
points) are proposed; account for copies separately. Test restore plus referential
integrity before scheduling. Backup location, key handling and operator are pending.

## Scheduling, retries and observability

Manual CLI is the first operating mode. After Gate C, propose a systemd timer on
an existing approved private Linux host at **06:17 UTC daily** (06:17 Ghana time),
with up to five minutes of jitter and a no-overlap lock. A missed run performs one
catch-up, not a burst. A laptop that is off does not provide continuous coverage;
do not call a transient development environment a production host.

Poll each approved endpoint once per run, sequentially. Use ETag/Last-Modified
conditionals only when the endpoint supplies them. A 304 records a successful
check with no new payload. If the checkpoint exists without its backing snapshot,
discard the conditional and make one bounded full request. Initial CISA fetch
is the whole catalog; vendor feeds cover their current window only. No deep
pagination or automatic backfill. Check source policy/robots at onboarding and
at least weekly or on redirects/terms changes; uncertainty pauses the source.

Proposed budgets: 5-second connect timeout, 20-second read timeout, 60-second
total attempt deadline, at most three attempts per source per run, and a
10-minute whole-run deadline. Retry timeouts, transient network errors, 429 and
5xx with exponential backoff/jitter; respect Retry-After. If it exceeds the run
budget, record next-eligible time and defer. Do not repeatedly retry 401/403/404,
schema errors, unsafe URLs or oversized input. Suspend a source after three
consecutive failed runs pending operator review. All failures produce safe codes.

An unexpected adapter error must still let other adapters run. Invalid individual
feed entries may be quarantined with reason and locator while valid entries
commit; a malformed whole feed or invalid KEV envelope rejects that source run.
Partial acceptance must be explicit in counts and checkpoints, with enough
retained data to reprocess rejected entries; never silently skip them. No process
should claim a complete run when a source failed or is disabled.

Private operational summaries contain source ID, run ID, attempt count,
new/unchanged/revised/rejected counts, duration, bytes and safe error codes.
Exclude payloads, article titles, arbitrary exception text and credential URLs.
Track last successful check separately from latest source publication; quiet
feeds are not necessarily broken. Flag checks older than 48 hours for operator
review, without automatically messaging external services.

GitHub Actions stays lint/fixture CI. Hosted scheduled jobs can be delayed or
dropped and public schedules can disable after inactivity; they also lack a
chosen private durable evidence store. These are reasons to defer hosted ingestion,
not to add a public database artifact. See [GitHub scheduling documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).

## Security and input budgets (F3/F7)

- Allowlist exact HTTPS endpoint hosts/paths from the approved source register,
  port 443 only. Do not fetch links found in entries, IOCs, notes or HTML.
- Reject userinfo, unexpected schemes/ports, IP literals and ambiguous hosts.
  Resolve all A/AAAA records and reject loopback, private, link-local, multicast,
  unspecified and other non-global ranges, including cloud metadata and IPv4-mapped
  IPv6. Validate every redirect (maximum three) and connection destination; pin
  approved resolution for the connection or use controlled egress to prevent DNS
  rebinding. Preserve TLS certificate/hostname verification. Explicitly configure
  proxy use; do not inherit an unchecked proxy as an SSRF bypass.
- Limit transferred and decompressed bytes independently: **8 MiB per KEV body**,
  **2 MiB per RSS body**, with bounded parser work and no automatic cap increase.
  The KEV exception revises the earlier blanket 2 MiB proposal to allow catalog
  growth; it is not a measurement of current wire size. Cap parsed items at 10,000
  KEV entries and 500 feed entries per response; exceeding limits fails explicitly.
- Proposed character limits: title 512, URL 4,096, identifier/publisher 256,
  excerpt 65,536, other ingestion text 8,192. Source-native GUIDs use the URL cap
  when they are URLs. Keep originals in a permitted bounded snapshot; reject
  oversize normalized fields instead of silently truncating evidence. Report-body
  limits remain a later-stage decision; no reporting implementation in M1.
- Disable DTDs, entities and external resource loading; reject malformed or
  deeply nested XML, decompression bombs, dangerous encodings and hostile HTML.
  Retain a summary as inert source evidence; never render or execute scripts or
  feed instructions. If a display is added later it needs separate escaping.
- Keep credentials absent for these public routes; any future secret requires
  separate approval, environment/secret-store injection and least privilege.
  Use synthetic public fixtures. No malware samples, sensitive source dumps,
  production snapshots or raw failures in Git or CI.
- TLP metadata is not access control. Keep all M1 evidence private; F4 inheritance
  and authenticated human publication approval must be resolved before an exporter.

## Cost and capacity proposal

| Item | Expected cost / ceiling |
| --- | --- |
| Software, KEV/public RSS routes | $0 license/API charges proposed; no paid APIs, LLMs or purchases enabled |
| Existing approved host | $0 incremental service spend; electricity, connectivity, operator time and existing hardware are not free and are not priced here |
| Volume | Three endpoints × one daily run ≈ 90 primary fetches/month; up to 270 attempts with retries, plus bounded policy checks. At body caps, about 360 MiB/month without retries or 1,080 MiB with all attempts at cap, before headers/policy checks. |
| Private storage/backups | 2 GiB live cap; seven full backups could add up to 14 GiB. Provision only on existing approved encrypted storage; otherwise pause for a storage decision. |
| GitHub CI | Standard public-repository runners are currently free; no ingestion artifacts, larger runners or new paid storage. [GitHub billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions) |
| Future always-on hosting | Not selected or purchased. A $5–10/month planning allowance could be considered later, not a verified vendor quote or authorized spend. |

The proposed hard incremental paid-service budget is **$0** until the owner
approves a different budget. Record actual request counts, disk usage and run
duration during the manual pilot; revisit assumptions before increasing cadence.

## Acceptance criteria (not yet met)

| ID | Requirement | Verification required in implementation PRs |
| --- | --- | --- |
| M1-AC1 | Approved scope and all three source onboarding records | Versioned approval plus per-source endpoint, terms/retention, robots and runtime evidence. If a source cannot be cleared, obtain an explicit revised scope; do not silently declare completion. |
| M1-AC2 | Adapters independently replaceable | Fixture tests for each adapter and a narrow dependency test for the composition layer; no adapter-to-storage or cross-adapter concrete imports. |
| M1-AC3 | Provenance survives persistence | Round-trip exact source text/URLs, native IDs, nullable dates/precision, retrieval/final URLs, hashes, source locator and parser version through SQLite and snapshots. Missing/date-only values never become fabricated timestamps. |
| M1-AC4 | Idempotency and source changes | Replaying a response creates no duplicate evidence; altered entry creates a linked revision; reordering/304/restart does not change identity; conflicting IDs reject; RSS disappearance does not delete evidence. |
| M1-AC5 | Failure isolation and bounded retries | Fake transport proves timeout/429/5xx budgets and Retry-After deferral; permanent errors do not loop; one source/parser failure leaves other sources successful; partial runs are reported honestly. |
| M1-AC6 | Fetch and parser safety | Tests cover redirect-to-private hosts, DNS rebinding strategy, IPv4/IPv6 special ranges, TLS verification, unexpected proxies, DTD/entity input, malformed/deep XML, compression and every size boundary (at/above limit). No untrusted link is fetched. |
| M1-AC7 | Safe durable state | Temporary-store integration tests for same-ID conflict, foreign keys, crash/disk-full rollback, checkpoint retry, orphan recovery, no-overlap lock and backup restore; no source content in logs or public artifacts. |
| M1-AC8 | Honest scope and human boundary | No LLM, enrichment, attribution, report generation or exporter; unknown confidence/Ghana relevance/TLP preserved; existing draft-only and human-role tests remain green. |
| M1-AC9 | Operational pilot | After Gate B, one approved manual run per source plus repeat/conditional check, bounded and privately recorded. After Gate C only, validate timer, missed-run behavior, stale checks and disable/rollback procedure. |
| M1-AC10 | Reproducible review | Ruff check/format and pytest pass on CI Python versions; offline tests block real network; only the explicitly tracked F4 xfail remains unless separately resolved; update contracts, status, decisions and handoff with actual results. |

## Implementation sequence after approval

1. Confirm Gate A and resolve contract/host/rights decisions; recheck feasibility
   through permitted tools. Document any source-specific restriction before coding.
2. Add reviewed retrieval/identity/limit contracts and fixture tests, then private
   storage/recovery behind interfaces. Keep existing V1 compatibility explicit.
3. Add each adapter separately with shared bounded transport/parser tests; compose
   a manual runner with static registration and failure isolation. Remain offline
   until source-specific Gate B is satisfied.
4. Execute the authorized manual pilot, review observed costs/coverage, then add
   an operator runbook for enable/disable, backup/restore and optional Gate C timer.
   Stop collection by disabling the timer/source; preserve evidence and checkpoints
   for audit. Revert code only with compatible schema/backup recovery, never by
   deleting evidence or rolling back blindly over newer records.

Owner review is requested for D004–D008: source scope/rights process, contract
extensions, SQLite/private snapshots, host/operator, daily schedule, limits,
retention/backups and $0 incremental budget. Record conditional approvals
explicitly. Until then, the next authorized work is plan revision only.
