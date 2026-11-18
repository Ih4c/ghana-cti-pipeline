# M1 — Minimal intelligence collection plan

- Specification version: **1.2**
- State: **proposed — no implementation increment is approved**
- Updated: 2026-11-18
- Planning baseline: main `1e5c2bca28077406acae576b88e77114f1288450`
- Approval: pending owner review; record exact version/scope in [DECISIONS.md](../DECISIONS.md).
- Supporting evidence: [source feasibility, 2026-11-18](M1_SOURCE_FEASIBILITY.md).

## Revision and readiness record

Versions 1.0 (PR #4) and 1.1 (PR #5) are merged planning history, not
implementation approvals. Version 1.2 records the owner's accepted hybrid
strategy (D018): permitted CISA catalog snapshots, metadata-first vendor RSS,
optional permitted excerpts, and the existing report template retained unchanged.
Technical refinements remain proposed/open: D011–D017 and D019–D021 distinguish
response digests from retention, additive V2 evidence from V1, and metadata-only
304 checkpoints from raw-backed checkpoints. See [hybrid evidence and retention](M1_EVIDENCE.md)
and the [revised PR plan](M1_READINESS.md). Prior versions remain in Git history.

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
| `microsoft-security-blog` | Registered RSS URL; GUID, otherwise original entry URL | Preserve approved feed title, link, GUID, publisher and date/precision; no summary by default. Optional exact excerpts require a specific permission. Store original publication text and parsed timezone when supplied; malformed dates are flagged, not guessed. GUID stability and description availability need payload verification. |
| `google-threat-intelligence` | Publisher-linked FeedBurner RSS; GUID, otherwise original entry URL | Same metadata-first mapping, with distinct feed/final/article URLs and source attribution. Do not use the premium intelligence API. Validate any claimed original-link extension before using it. |

All source entries retain configured source ID, publisher, original URL,
source-native ID, original date/precision when available, UTC retrieval time,
adapter/parser version and evidence linkage. Missing publication dates remain
unknown. CISA's catalog date is not copied onto every CVE as publication time.
Public availability and CC0 do not automatically set TLP:CLEAR; retain supplied
TLP if present, otherwise null and private handling. Confidence stays unknown;
no Ghana relevance claim is produced by collection.

Vendor summary retention is conditional on rights clearance. A raw RSS snapshot
may include full `content:encoded` articles even if only summaries are normalized.
Vendor processing must discard unapproved article fields after bounded in-memory
parsing and retain only approved metadata. Excerpts default to absent and require
field/length/use permission. No durable vendor raw snapshot is proposed. Metadata
and transient processing still need a documented rights basis before source
verification; accessibility is not a license. [Source policies](M1_EVIDENCE.md)
define exact retained fields, rights records and deletion/backup requirements.
Never silently truncate/rewrite evidence or fabricate V1's required excerpt.

## Architecture and contract evolution

Keep one Python distribution. The existing core contracts and protocol boundaries
remain the starting point; do not make adapters import concrete storage or each
other. Proposed composition:

```text
manual CLI / optional local timer
  -> explicit static adapter registry and per-source runner
  -> bounded HTTPS transport -> independent fetch/parse adapter
  -> normalization + revision identity -> storage interfaces
  -> private SQLite retained metadata + optional permitted CISA snapshot BLOBs
```

| Component | Proposed responsibility / test boundary |
| --- | --- |
| `core/` | Existing V1 domain contracts unchanged; additive retrieval/observation descriptors and later V2 hybrid evidence, identifiers, limits and safe error codes. No network/database dependencies. |
| `collectors/` | Separate CISA, Microsoft and Google adapters using fetch/parse separation. Shared injected HTTPS transport and RSS parser may remove duplication; source mapping/permissions remain separate. Parse functions never perform I/O. |
| `storage/` | Keep V1 EvidenceRepository; add explicit versioned evidence/retrieval/state protocols for both representations with SQLite. Enforce immutable ID/content semantics and preserve source-local revisions. |
| New `orchestration/` and CLI | Compose explicit adapters, transport and repositories, isolate failures, apply per-source budgets/checkpoints and return a run summary. This is a documented composition-layer exception to the current component dependency test, to be narrowly tested in the approved implementation. |
| Later-stage packages | No change to triage, enrichment, analysis or reporting behavior. |

Use standard-library SQLite/UUID/hash tools, existing Pydantic contracts, a small
maintained open-source HTTP client with streaming/timeouts, and a hardened XML
parser (for example defusedxml). Pin and review any additions in uv.lock. HTTP
client selection must demonstrate the SSRF controls below; a client library alone
does not supply them. Avoid a broker, microservices, browser automation or dynamic
plugin imports at this scale.

The [hybrid model](M1_EVIDENCE.md) defines common source/publisher/native identity,
original URL and publication precision, retrieval/HTTP metadata, adapter/schema
versions, policy references and revision lineage for both representations:

- **Raw-snapshot-backed:** permitted complete CISA entity bytes, original fields,
  response digest and exact source-item locators; backing availability is explicit.
- **Metadata-only:** approved field projection plus optional permitted excerpt,
  its retained-content digest and optional observed response digest. No raw artifact
  association; a response hash is not an archived or independently reproducible body.

Keep existing V1 SourceItem/EvidenceRecord and Collector/FetchedDocument/
EvidenceRepository shapes unchanged. V1's nonblank excerpt rule is not weakened.
Propose additive EvidenceRevisionV2 in a later increment; never substitute a title,
placeholder or generated summary as an excerpt. New retrieval descriptors in
M1-01 record receipt, not storage; retention association occurs only after policy
validation/commit. Schema versions are distinct from the milestone version.

Distinguish complete 200 receipt, bodyless 304 checks and transport failures from
successful processing/storage. An eligible 304 references the committed 200 and
its valid processing manifest, not necessarily a retained raw body. No fresh
per-item observation or publication date is created. D019 specifies both modes.

D012 keeps immutable revision identity separate from retrieval observations.
Repeated allowed retained content reuses an available revision; A→B→A adds history
without editing parent links. Identity includes representation/profile and retained
field digest, not retrieval time. Metadata equality does not prove article equality.
Keep sources distinct; CISA absence is a presence event, RSS window absence is not
retraction, and article/IOC URLs remain references that are never auto-fetched.

## Private persistence, retention and recovery

D013/D019 propose one private SQLite database with foreign keys and atomic source
batches: retained projections/evidence, retrieval descriptors, processing manifests,
observations, source state, policy references and safe error/availability events.
Only approved raw-backed acquisitions may store content-addressed BLOBs. Metadata-only
writes accept typed projections, never vendor body bytes. Snapshots and records
must share policy-aware ownership; a hash does not confer retention rights.

The [storage/lifecycle design](M1_EVIDENCE.md) specifies the two commit shapes,
no I/O within transactions, operation idempotency, conflicting-ID rejection,
crash/disk-full rollback, one writer/run, schema compatibility and consistent
backup/restore. Do not use a second snapshot directory or orphan-file subsystem.
A parser or storage failure never advances the successful checkpoint.

Use a dedicated least-privilege account, owner-only files and encrypted host
storage outside the checkout/web roots/public sync/Actions artifacts. SQLite is
not encrypted by default. Vendor raw bytes stay in bounded memory only; prohibit
spooling, caches, raw diagnostics and memory dumps. Validate the host's swap/dump
and backup behavior before live use. Unexpected restricted markings stop that
source with safe diagnostics; never downgrade, export or retain rejected raw
vendor bytes for quarantine. See D020 for synthetic leak tests and host limits.

Retain the proposed CISA 365-day reporting target and 30-day unreferenced-artifact
cap only within approved policy/capacity. Vendor metadata, excerpts, response hashes,
HTTP metadata and audit records require their own maximum deadlines before B2;
there is no inherited 365-day entitlement. No durable vendor raw retention.
Rights changes/expiry apply to live rows, WAL/free pages and every backup. Preserve
only independently permitted tombstones; invalidate affected checkpoints and mark
citations unavailable. Approve/test deletion and isolated restore procedures before
activation. A cited record does not override required deletion, and a 304 does not
extend rights. Do not silently purge cited records just to create disk capacity.

Keep the 2 GiB live-store cap, warning at 80%, 512 MiB/day transfer cap and proposed
seven encrypted daily restore points at an approved private location. Stop before
capacity instead of buying storage. CISA alone at 8 MiB/day of changed snapshots
exceeds 2 GiB/year before records/indexes; metadata-first feeds reduce storage but
not downloaded bytes. Measure pilot growth before selecting capacity/retention.
Expiry may require retiring backups sooner than seven days. Operator, key handling,
backup location and verifiable purge procedure are unresolved. Disable source/timer
to stop collection; preserve still-permitted evidence and use compatible schemas/
backups for code rollback, never blindly downgrade newer records.

## Scheduling, retries and observability

Manual CLI is the first operating mode. After Gate C, propose a systemd timer on
an existing approved private Linux host at **06:17 UTC daily** (06:17 Ghana time),
with up to five minutes of jitter and a no-overlap lock. A missed run performs one
catch-up, not a burst. A laptop that is off does not provide continuous coverage;
do not call a transient development environment a production host.

Poll approved endpoints sequentially once per run. D019's [conditional-request
rules](M1_EVIDENCE.md) scope validators to the exact source/endpoint/request variant,
supported Vary fields and unchanged processing profile. A fully committed 200
manifest and intact retained records are required. Raw-backed mode also requires
its verified artifact; metadata-only mode deliberately does not. A 304 records a
check against that original 200, never another 304 or new item observations.
Missing/corrupt required state allows one unconditional request within the remaining
budget only if rights are still valid. Expired rights pause instead. No automatic
re-fetch to restore deleted content. Unsupported Vary disables conditionals;
unsupported no-store directives pause for policy review. No article-access or
content-authenticity claim follows from an ETag, response hash or 304.

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
Log safe failure code/count/locator only; locators must be bounded structural
positions, not source text or raw exception messages. Discard rejected raw vendor
bytes on every path. Only permitted raw-backed sources may retain rejected data
under a separate policy. Other sources still run.
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
  rejected. Proxy support is deferred pending a separately reviewed design.
  Use an approved host with permitted direct egress;
  this is not authorization to bypass the current environment proxy.
- Limit transferred and decompressed bytes independently: **8 MiB per KEV body**,
  **2 MiB per RSS body**, with bounded parser work and no automatic cap increase.
  The KEV exception revises the earlier blanket 2 MiB proposal to allow catalog
  growth; it is not a measurement of current wire size. Cap parsed items at 10,000
  KEV entries and 500 feed entries per response; exceeding limits fails explicitly.
- Proposed character limits: title 512, URL 4,096, identifier/publisher 256,
  excerpt 65,536, other ingestion text 8,192. Source-native GUIDs use the URL cap
  when they are URLs. Keep originals only when raw retention is approved; reject
  oversize normalized fields instead of silently truncating evidence. Report-body
  limits remain a later-stage decision; no reporting implementation in M1.
- D015 proposes UTF-8 input only (optional UTF-8 BOM), maximum parser depth 64,
  and response headers capped at 32 KiB. Unsupported encodings fail explicitly;
  adapting to a verified vendor format requires review, not permissive fallback.
  Disable DTDs, entities and external resource loading; reject malformed/deep
  XML, decompression bombs and invalid JSON. Ignoring full-article fields never
  bypasses byte/depth/item limits; default vendor projections omit them.
  Treat embedded HTML as inert text, not as a reason to execute/fetch anything.
  Never render scripts or feed
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
| M1-AC3 | Provenance survives persistence | Round-trip approved fields, source URLs/native IDs, date precision, retrieval/HTTP metadata, policy and adapter/schema versions for both representations. Verify raw and retained digests separately; metadata-only records never imply an archive. Missing dates remain unknown. |
| M1-AC4 | Idempotency and source changes | Replaying a response creates no duplicate evidence; changed retained fields create a revision linked to the logical source key/history; A→B→A reuses available A; metadata equality never asserts article equality; reordering/304/restart does not change identity; conflicting IDs reject; RSS disappearance does not delete evidence. |
| M1-AC5 | Failure isolation and bounded retries | Fake transport proves timeout/429/5xx budgets and Retry-After deferral; permanent errors do not loop; one source/parser failure leaves other sources successful; partial runs are reported honestly. |
| M1-AC6 | Fetch and parser safety | Tests cover redirect-to-private hosts, DNS rebinding strategy, IPv4/IPv6 special ranges, TLS verification, unexpected proxies, DTD/entity input, malformed/deep XML, compression and every size boundary (at/above limit). No untrusted link is fetched. |
| M1-AC7 | Safe durable state | Temporary-store tests for both commit shapes, same-ID conflict, foreign keys, crash/disk-full rollback, idempotent retry and locking; metadata-only 304 works without raw bytes, raw-backed 304 fails without required backing; no raw vendor content in DB/WAL/backup/log/artifact; source-specific expiry and isolated restore tested. |
| M1-AC8 | Honest scope and human boundary | No LLM, enrichment, attribution, report generation or exporter; unknown confidence/Ghana relevance/TLP preserved; existing draft-only and human-role tests remain green. |
| M1-AC9 | Operational pilot | After explicit B1 verification approval and B2 manual activation, one approved manual run per source plus repeat/conditional check, bounded and privately recorded. After Gate C only, validate timer, missed-run behavior, stale checks and disable/rollback procedure. |
| M1-AC10 | Reproducible review | V1 shapes/excerpt validation remain unchanged; additive V2 supports absent excerpts. Ruff check/format and pytest pass on CI Python versions; offline tests block real network; only the explicitly tracked F4 xfail remains unless separately resolved; update contracts, status, decisions and handoff with actual results. |

## Implementation sequence and approval request

The [ordered PR plan](M1_READINESS.md) follows contracts → identity → SQLite and
recovery → transport/parsing → separate adapters → manual CLI/offline integration
→ separately approved source verification/manual activation → separately approved
scheduling. Each increment has dependencies and acceptance tests. Host/rights
selection blocks live work, not approved synthetic core or temporary-store tests.

**Recommended first approval is M1-01 only under v1.2/D011 and the descriptor
portion of D019:** additive core retrieval/observation metadata contracts,
synthetic fixtures, focused offline
tests and related documentation; preserve existing V1 shapes/protocols and add
no dependencies. This does not approve V2 evidence implementation, hashing behavior,
persistence, transport, parsing, adapters,
live requests, deployment, scheduling, paid services or later increments.

D018 accepts strategic direction only; D004–D008, D011–D017 and D019/D020 remain
proposed; D021 is open. Review the explicit changes and record
actual approval/version/scope in DECISIONS before writing code. Until then, the
next authorized work is documentation revision only. No source content is fetched
or archived during this readiness task.
