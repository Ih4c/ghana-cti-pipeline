# M1 — Minimal intelligence collection plan

- Specification version: **1.1**
- State: **proposed — no implementation increment is approved**
- Updated: 2026-11-18
- Planning baseline: main `50224b35c1b27bbaca0fb1551bdf4b8205cb7de8`
- Approval: pending owner review; record exact version/scope in [DECISIONS.md](../DECISIONS.md).
- Supporting evidence: [source feasibility, 2026-11-18](M1_SOURCE_FEASIBILITY.md).

## Revision and readiness record

Version 1.0 was proposed in merged PR #4. Version 1.1 explicitly proposes
corrections D011–D017; none is accepted by this document alone. The
[readiness review and PR execution plan](M1_READINESS.md) records contradictions,
their corrections, exact first-increment scope and acceptance tests. Key changes:
additive V1-compatible metadata, bodyless 304 references, stable revision reuse,
SQLite BLOB snapshots instead of a separate directory, source-batch atomicity,
direct-only transport, bounded parser/retry policy, and separate verification and
activation gates. The prior proposal remains available in Git history.

## Outcome, scope and approval gates

Collect source-attributed evidence from three independently replaceable candidate
adapters: CISA KEV JSON, Microsoft Security Blog RSS, and the official Google
Threat Intelligence/Mandiant RSS feed. Store normalized records and retrieval
evidence privately, deduplicate repeat observations, retain revisions, and let
one source fail without losing others. These sources support vulnerability and
research coverage for Ghanaian defenders; they are not proof of local targeting.

This readiness PR contains documentation only. **Gate A:** owner approves a
named increment/version before related application code is written. Approval of
M1-01 alone is not approval of storage, transport or adapters. **Gate B1:** separate
source-specific approval permits bounded live verification, with a rights basis
covering the bytes received/retained and an approved private host. **Gate B2:**
after verification passes, separate approval permits manual source collection.
**Gate C:** recurring scheduling requires explicit activation after an approved
manual pilot. No Gate A/B1/B2/C approval is recorded. Offline synthetic increments
do not require a production host or vendor rights, but still require Gate A.

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

Vendor summary retention is conditional on rights clearance. A raw RSS snapshot
may include full `content:encoded` articles even if only summaries are normalized.
Rights must cover the complete snapshot and backup
lifetime before any vendor fetch/retention. Otherwise disable the source until
a separately reviewed metadata-only design can preserve honest provenance.
Never silently truncate/rewrite evidence to satisfy a field.

## Architecture and contract evolution

Keep one Python distribution. The existing core contracts and protocol boundaries
remain the starting point; do not make adapters import concrete storage or each
other. Proposed composition:

```text
manual CLI / optional local timer
  -> explicit static adapter registry and per-source runner
  -> bounded HTTPS transport -> independent fetch/parse adapter
  -> normalization + revision identity -> storage interfaces
  -> private SQLite metadata + permitted content-addressed snapshot BLOBs
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

`FetchedDocument` currently lacks HTTP outcomes and transport metadata. Add
independent versioned retrieval/observation types as specified in
[M1_READINESS.md](M1_READINESS.md), without changing existing V1 models or
Collector/FetchedDocument/EvidenceRepository signatures in M1-01. New type versions
are separate from this milestone's version. Later fetch-interface changes need a
reviewed integration; old serialized V1 data must still validate unchanged.

Distinguish 200 transport success, 304 not-modified and transport failure from
parsing/storage success. A 200 references a bounded snapshot; a 304 has no body
and names the committed, fully processed 200 representation. Storage validates
cross-record references. A 304 records a successful check without new per-item
observations or evidence. A parser failure cannot become a successful checkpoint.

D012's proposed identity profile separates operation IDs, logical source keys,
content revision IDs and chronological observations. Deterministic revision IDs
exclude retrieval time. Reuse an existing revision's complete immutable evidence
(including its original retrieved_at) and add observations rather than overwriting
that evidence. A→B→A reuses A without cyclic predecessor links. parent_evidence_ids
remain for genuine derivation; temporal history belongs to observations. The
readiness review defines canonicalization and vector requirements for M1-02.

Preserve original references and full snapshot digest independently from the
existing excerpt hash. Never silently canonicalize away meaningful URL queries,
fetch referenced links or merge distinct sources. CISA disappearance is a
source-presence event, not deletion; a rolling RSS window does not prove retraction.

## Private persistence, retention and recovery

D013 proposes one private SQLite database with foreign keys and transactions,
including content-addressed BLOBs for permitted response bytes. This revises the
v1.0 separate-directory proposal to remove a two-resource commit/recovery protocol.
Logical tables cover retrievals, immutable evidence revisions, per-item observations, source state,
runs and safe error events. Index source/native identity and revision digest;
enforce same-ID/same-content no-op and same-ID/different-content rejection.
Snapshot keys are SHA-256 digests, never untrusted paths. No external snapshot
files or orphan-file collector are needed for this bounded M1 backend.

Use a dedicated least-privilege account, owner-only files/directories and encrypted
host storage. SQLite is not encrypted by default. Store outside the checkout,
public web roots, synced public folders and Actions artifacts/caches. M1 accepts
only approved public endpoints; if restricted markings unexpectedly appear,
stop that source and record a safe failure for private review. Discard the rejected
payload unless separately approved retention covers it; never downgrade or export
it. M1 does not add a quarantine subsystem.

Validate the complete source batch before opening the write transaction.
Atomically commit snapshot BLOB, retrieval/processing metadata, immutable evidence,
observations and conditional checkpoint in one transaction; perform no network
I/O while holding it. Failure rolls back the source batch. A separately recorded
safe failure event never advances a checkpoint. Reuse of an operation ID is a
no-op only if its contents match. Allow only one writer/run. Test interrupted
commits, disk-full, conflicting IDs and unsupported schema versions. Use a
consistent SQLite backup and verify hashes, foreign keys and checkpoints on
restore; never blindly copy a live database file or downgrade newer data.
The operational runbook must stop collection by disabling the source/timer while
preserving evidence and checkpoints. Revert code only with compatible schema and
backup recovery, never by deleting evidence or blindly rolling back newer records.

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
Retention/permission expiry applies to every backup, not only the live store.
At the daily 12 MiB
payload maximum, 365 days of changed snapshots exceeds 4 GiB before indexes;
2 GiB is a stop limit, not a guarantee of a year of coverage. Review measured
pilot growth and rights before selecting capacity or revised retention. No
permission-independent 365-day archival promise or automatic destructive purge.

## Scheduling, retries and observability

Manual CLI is the first operating mode. After Gate C, propose a systemd timer on
an existing approved private Linux host at **06:17 UTC daily** (06:17 Ghana time),
with up to five minutes of jitter and a no-overlap lock. A missed run performs one
catch-up, not a burst. A laptop that is off does not provide continuous coverage;
do not call a transient development environment a production host.

Poll each approved endpoint once per run, sequentially. Conditional headers are
scoped to the same source, endpoint and fixed request representation headers;
unsupported Vary behavior disables conditionals. Only a fully processed committed
200 response with a verified retained snapshot can be a conditional checkpoint.
A valid 304 may update check time/returned validators, but must reference that 200
directly, never another 304. No item parsing or new evidence occurs. Missing or
corrupt backing data invalidates the conditional and consumes a remaining attempt
on one unconditional fetch; no remaining budget means defer. An unsolicited 304
is a protocol failure. These rules are tested with synthetic records, not live calls.

Initial CISA fetch is the whole catalog; vendor feeds cover their current window
only. No pagination or backfill. Source policy/robots checks remain part of B1
and are refreshed at least weekly/when redirects or terms change after activation;
uncertainty pauses that source. Checks do not authorize bypassing restrictions.

D015 proposes 5-second connect, 20-second read, 60-second total attempt deadlines,
maximum three top-level attempts and **180 seconds total per source**, including
backoff, redirects and unconditional recovery, within the 10-minute run deadline.
Redirects are bounded within the attempt, not fresh retry allowances. Retry only
transient network errors, 429 and 5xx with exponential backoff/jitter; honor
Retry-After by recording next-eligible time if it does not fit the budget. 401/403/
404, unsafe URLs, schema/parser/size errors do not retry. Suspend after three
consecutive failed runs pending review; a disabled source does not block others.

To keep M1 reviewable, reject the whole source batch on any invalid item, conflicting
source-native IDs or malformed envelope. Keep previous validators/checkpoints.
Log safe failure code/count/locator only; discard raw rejected bytes unless a
separately approved retention policy permits them. Other sources still run.
Per-item quarantine, partial checkpoints and replay tooling are deferred. A valid
empty RSS channel is a successful empty observation set, not a retraction;
malformed/empty bodies and an invalid KEV count/envelope fail explicitly.

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
  IPv6. Validate every redirect (maximum three) and connection destination; bind
  the connection to validated resolved IPs while preserving the original TLS
  hostname/SNI; test DNS changes between validation and connect. Revalidate each
  hop and retry. No automatic library redirects or second unchecked DNS lookup.
  Preserve TLS certificate/hostname verification. D014 proposes direct-only mode
  with inherited proxy environment disabled and explicit proxy configuration
  rejected. Proxy support is deferred pending a
  separately reviewed design. Use an approved host with permitted direct egress;
  this is not authorization to bypass the current environment proxy.
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
- D015 proposes UTF-8 input only (optional UTF-8 BOM), maximum parser depth 64,
  and response headers capped at 32 KiB. Unsupported encodings fail explicitly;
  adapting to a verified vendor format requires review, not permissive fallback.
  Disable DTDs, entities and external resource loading; reject malformed/deep
  XML, decompression bombs and invalid JSON. Treat embedded HTML as inert text,
  not as a reason to execute/fetch anything. Never render scripts or feed
  instructions; any future display needs separate escaping.
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
| Volume | Three endpoints × one daily run ≈ 90 primary fetches/month; up to 270 attempts with retries, plus bounded policy checks. At body caps, about 360 MiB/month without retries or 1,080 MiB with all attempts at cap, before bounded redirect/header/policy overhead. |
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
| M1-AC4 | Idempotency and source changes | Replaying a response creates no duplicate evidence; altered entry creates a revision linked to the logical source key and observation history; A→B→A reuses A; reordering/304/restart does not change identity; conflicting IDs reject; RSS disappearance does not delete evidence. |
| M1-AC5 | Failure isolation and bounded retries | Fake transport proves timeout/429/5xx budgets and Retry-After deferral; permanent errors do not loop; one source/parser failure leaves other sources successful; partial runs are reported honestly. |
| M1-AC6 | Fetch and parser safety | Tests cover redirect-to-private hosts, DNS rebinding strategy, IPv4/IPv6 special ranges, TLS verification, unexpected proxies, DTD/entity input, malformed/deep XML, compression and every size boundary (at/above limit). No untrusted link is fetched. |
| M1-AC7 | Safe durable state | Temporary-store integration tests for same-ID conflict, foreign keys, crash/disk-full rollback of BLOBs and checkpoints, idempotent operation retry, no-overlap lock and consistent backup restore; no source content in logs or public artifacts. |
| M1-AC8 | Honest scope and human boundary | No LLM, enrichment, attribution, report generation or exporter; unknown confidence/Ghana relevance/TLP preserved; existing draft-only and human-role tests remain green. |
| M1-AC9 | Operational pilot | After explicit B1 verification approval and B2 manual activation, one approved manual run per source plus repeat/conditional check, bounded and privately recorded. After Gate C only, validate timer, missed-run behavior, stale checks and disable/rollback procedure. |
| M1-AC10 | Reproducible review | Ruff check/format and pytest pass on CI Python versions; offline tests block real network; only the explicitly tracked F4 xfail remains unless separately resolved; update contracts, status, decisions and handoff with actual results. |

## Implementation sequence and approval request

The [ordered PR plan](M1_READINESS.md) follows contracts → identity → SQLite and
recovery → transport/parsing → separate adapters → manual CLI/offline integration
→ separately approved source verification/manual activation → separately approved
scheduling. Each increment has dependencies and acceptance tests. Host/rights
selection blocks live work, not approved synthetic core or temporary-store tests.

**Recommended first approval is M1-01 only under v1.1/D011:** additive core
retrieval/observation metadata contracts, synthetic fixtures, focused offline
tests and related documentation; preserve existing V1 shapes/protocols and add
no dependencies. This does not approve persistence, transport, parsing, adapters,
live requests, deployment, scheduling, paid services or later increments.

D004–D008 and new D011–D017 remain proposed. Review the explicit changes and record
actual approval/version/scope in DECISIONS before writing code. Until then, the
next authorized work is documentation revision only. No source content is fetched
or archived during this readiness task.
