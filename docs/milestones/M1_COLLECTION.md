# M1 — Full-text intelligence collection plan

- Specification version: **1.3**
- State: **strategy accepted; M1-01/M1-02a data contracts approved only; remaining technical design proposed**
- Updated: 2026-11-19
- Verified planning baseline: main `ccd81278472c7847287ffcf20988629435f2c999`
- Approval boundaries: [DECISIONS.md](../DECISIONS.md), D022–D024.
- Evidence: [historical feasibility and owner-reported observations](M1_SOURCE_FEASIBILITY.md).

## Revision and intended outcome

PR #6 merged v1.2's hybrid plan; its metadata-first vendor direction (D018) is now
superseded by the owner's v1.3 instruction, D022. Retain complete permitted CISA
catalog entries and full article content supplied by the Microsoft and Google
feeds, with attribution and immutable provenance, for future original Ghana-focused
intelligence. Metadata-only vendor collection is not the intended final capability.
If rights or completeness fail, block the source and resolve them; do not quietly
substitute metadata, scrape article pages or claim three-source completion.

PR #7 merged this strategy without implementation authorization. Subsequent
[owner approval on PR #7](https://github.com/Ih4c/ghana-cti-pipeline/pull/7#issuecomment-6996754396)
authorizes **M1-01 under v1.3 only**, D011 and D019 retrieval/observation
descriptors, synthetic tests and related documentation. After PR #8 merged,
[separate owner approval](https://github.com/Ih4c/ghana-cti-pipeline/pull/8#issuecomment-6997113844)
authorizes M1-02a D019/D024 data contracts only. M1-02b onward, source access and
operational gates remain unapproved. Earlier v1.2 work is not
authority to proceed.
Historical versions remain in Git, not active scope. Existing V1 contracts,
permanent guidance, authoritative report template and human workflow are preserved.

## Source mapping and permission boundaries

| Source ID | Endpoint / native identity | Required content and verification state |
| --- | --- | --- |
| `cisa-kev` | Existing official mirror JSON in the source register; CVE ID | Complete permitted entry/original fields and catalog context. Historical JSON/schema/CC0 checks exist; runtime, robots/access and activation checks remain incomplete. dateAdded/dueDate are catalog dates, not publication or Ghanaian legal duties. |
| `microsoft-security-blog` | Existing registered RSS endpoint; GUID, otherwise exact original article URL | Complete `content:encoded` article content. Owner reports observing this on 2026-11-18; field namespace, completeness, size and behavior require independent B1 confirmation. Full-text rights unresolved. |
| `google-threat-intelligence` | Existing publisher-linked FeedBurner RSS endpoint; GUID, otherwise exact original article URL | Complete `description` article content. Owner reports observing this on 2026-11-18; complete-body mapping and behavior require independent B1 confirmation. Applicable terms/robots and full-text rights unresolved. |

Configured/final feed URLs and original article URL stay distinct. Preserve
publisher, native ID, supplied publication date/precision, retrieval times,
HTTP/validator metadata, adapter/parser/schema versions and policy ID/version.
Missing dates stay unknown; no confidence, Ghana targeting or attribution is
fabricated. Supplied TLP is preserved; absent marking is null, not TLP:CLEAR.
These sources support Ghanaian defenders but do not themselves prove local targeting.

D023 records owner-reported Microsoft copying/distribution/publication restrictions,
possible permitted-use limits, and the need to review applicable Google terms and
robots. The owner accepts identified operational/legal risks for private research.
That acceptance is not a license, copyright exception or authority to disregard
restrictions. The [rights matrix](M1_EVIDENCE.md) specifies unresolved uses and
routes: written permission, applicable grants or other legally supported grounds.
Commercial use/public republication requires a separate review and any necessary
written authorization. Technically accessible but prohibited/unresolved full-text
modes remain blocked. No terms or endpoints were fetched for this revision.

## Separate approval gates and exclusions

- **Gate A:** explicit approval of a named implementation increment/version in a
  GitHub PR comment. M1-01 and M1-02a have separate scoped approvals linked above; the
  documentation merge itself grants none.
- **Gate B1:** separate source-specific approval for bounded live verification,
  with an established basis for that access/processing scope, approved host and
  request/retention budget. Owner observations must be independently reconfirmed.
- **Gate B2:** separate manual collection/activation approval after B1, established
  full-text retention/derivation/backup rights, capacity and operator checks.
- **Gate C:** recurring scheduling approval after a successful approved pilot.

No network/source access is authorized here. Offline synthetic development still
requires Gate A. No article-page crawler, embedded-link following, historical
backfill, paid intelligence API, LLM calls, triage/ranking, IOC enrichment,
attribution, report generation, deployment or publication belongs to this task.
Later analytical judgments and publication remain human-controlled.

## Modular architecture and contracts

```text
manual CLI / separately approved daily timer
  -> static source registry and isolated source runner
  -> bounded HTTPS transport -> independent source adapter / safe parsing
  -> original content + deterministic sanitized HTML / plain text (vendor items)
  -> immutable identity, artifact associations and processing manifest
  -> private SQLite evidence/artifacts/observations/conditional checkpoint
```

| Component | Proposed responsibility / boundary |
| --- | --- |
| `core/` | Existing V1 unchanged; additive M1-01 metadata descriptors, later V2 source/derived artifact references, policy and manifest contracts. No network/storage implementation. |
| `collectors/` | Independent CISA/Microsoft/Google mappings; injected shared transport, pure safe parsers and versioned deterministic HTML/text transforms. No concrete storage imports or cross-adapter imports. |
| `storage/` | Separate reviewed protocols for V2/artifacts/state; implement existing V1 EvidenceRepository without changing its signature. Atomic source transactions and policy-aware retention. |
| Future composition/CLI | Static registry, source budgets, failure isolation and diagnostics. Narrow tested import-boundary exception; no dynamic plugin loading or autonomous publication. |
| Later-stage packages | No behavioral changes; human-led analysis/reporting and existing template authority preserved. |

Use existing Pydantic and standard-library SQLite/UUID/hash tools where suitable;
review minimal pinned open-source HTTP/XML/HTML sanitization dependencies only in
later approved increments. Avoid brokers, microservices and browser automation.
No dependencies are added by this documentation revision.

[M1_EVIDENCE.md](M1_EVIDENCE.md) defines the proposed `catalog_entry` and
`feed_full_text` modes, exact response versus extracted article distinctions,
original/sanitized/plain-text digests, immutable revisions and availability. V1's
required excerpt and narrow excerpt hash remain unchanged. Proposed V2 is additive;
no metadata fallback, synthetic excerpt or silent migration. M1-01 still describes
receipt/observations without bytes, retention claims or payload hashing behavior.
A descriptor alone cannot validate permissions, source truth or cross-record state.

## Storage, retention and capacity

Propose SQLite content-addressed BLOBs for permitted complete responses, original
items and required derivatives, alongside evidence, manifests, observations,
policies, safe failures and checkpoints. Validate and transform the whole source
batch before an atomic transaction; no network I/O within it. Failure does not
advance validators. Same operation ID/content is a no-op; conflicts reject.
Use foreign keys, single writer/run, explicit durable commits, schema checks,
crash/disk-full tests and consistent backups. BLOB tradeoffs and the deferred
separate-artifact alternative are explicit in [the storage design](M1_EVIDENCE.md).

All real source bodies remain in an approved private store outside Git, public
web roots/sync, PR attachments, logs and CI artifacts. Owner-only paths, least
privilege, encrypted host storage/backups and operator-controlled keys are required;
SQLite itself is not encrypted by default. Log only safe codes/counts and bounded
structural locators, not payload snippets or arbitrary exceptions. No real vendor
fixtures. Unexpected restricted markings pause that source; no downgrade/export.

Source-specific deadlines cover originals, derivatives, metadata, hashes, audit
records and every backup. Revocation/expiry pauses acquisition, invalidates
checkpoints and requires coordinated deletion; derivatives are not an escape from
source restrictions. Verify purge/compaction of DB/free pages/WAL, temporary files,
replicas and backup retirement; SQL DELETE alone is insufficient. Restore in
isolation against current rights/deletion state. Cite unavailable evidence honestly.
A proposed 365-day reporting target never overrides permissions or capacity.

Retain **2 GiB live-store cap**, warning at 80%, and **512 MiB/day transfer cap**;
account for WAL/temporary write headroom and stop before exceeding capacity.
At response maxima: 12 MiB/day of snapshots (~4.28 GiB/year). Including bounded
original/derived item copies, the proposed upper budget is 32 MiB/day (~11.4
GiB/year), before indexes/WAL. Thus 2 GiB cannot guarantee annual coverage and
holds fewer than 64 maximum-budget days after overhead. Deduplication benefits
must be measured, not promised. Capacity/retention conflicts require an explicit
owner decision, never automatic expansion, purchase or silent evidence purge.
Seven encrypted daily backups could add 14 GiB separately and must expire earlier
when rights require. Host/operator, backup location and purge procedure remain open.

## Polling, recovery and operational controls

Manual operation first after B2. After Gate C only, propose one scheduled cycle
per source per day at 06:17 UTC (Ghana time), up to five minutes jitter, no overlap.
A missed schedule produces at most one catch-up when eligible, not a burst. Persist
the cycle/attempt budget across restarts: catch-up, restart and recovery must not
create fresh allowances. Propose a minimum 24-hour interval between automatic
cycle starts; a late catch-up can skip the next nominal tick. Manual/verification
requests need their own explicit budget, not a loophole for repeated daily polling.

One cycle normally makes one conditional GET using ETag/Last-Modified. A cycle is
not one HTTP request: at most three top-level attempts include transient retries
and at most one unconditional recovery request. Every redirect (max three) stays
inside that attempt and the shared time/byte budget. No separate recovery cycle
or extra immediate poll. The [checkpoint rules](M1_EVIDENCE.md) require intact,
permitted full-text backing and manifest; a 304 creates only a check, not new
content or per-item observations. Use retained originals for local reprocessing
where possible. Changed rights pause, never trigger automatic re-acquisition.

Keep 5-second connect, 20-second read, 60-second attempt and 180-second total source
budgets including backoff, redirects, parsing/transforms and recovery; 10-minute
run maximum. Retry only transient network errors, 429 and 5xx with exponential
backoff/jitter. If Retry-After cannot fit, record next-eligible time and defer
until both it and the next permitted cycle allow a request. 401/403/404, unsafe
URLs and schema/parser/size errors do not retry; 403 pauses for access review,
not repeated immediate retries. Suspend after three consecutive failed cycles.
One source error leaves other sources runnable within their independent budgets.

Use a descriptive versioned User-Agent such as `GhanaCTIPipeline/<version>` with a
reviewed project contact URL, no personal identity or impersonation. Verify the
exact UA/path and every redirect against applicable robots/access restrictions
at onboarding and at least weekly or upon changes after activation. Policy checks
also consume a separately bounded, approved request budget; uncertainty pauses.
A publisher's stricter quota, no-automation rule or one-request limit overrides
project maxima: reduce attempts/redirect/recovery or block activation, never infer
permission from our default daily rule. No unauthorized proxy bypass.

Private operational summaries: source/run/cycle ID, attempts, bytes, duration,
new/unchanged/revised/rejected counts and safe error codes. Track last successful
check separately from publication date; flag stale checks over 48 hours for human
review without external messages. Actions remains offline lint/fixture CI, not
scheduled ingestion or a public evidence archive. Disable source/timer to stop;
preserve still-permitted evidence and use compatible schema/backups for rollback.

## Input and network security

- Exact approved HTTPS hosts/paths, port 443; no entry/IOC/HTML link requests.
  Reject credentials, ambiguous hosts, IP literals and unapproved schemes/ports.
- Resolve all A/AAAA and reject non-global/special ranges, metadata addresses and
  IPv4-mapped IPv6. Bind to validated IPs with original hostname/SNI and verified
  TLS certificate. Revalidate every redirect/retry; no second unchecked DNS lookup
  or automatic redirects. Disable inherited proxies; reject explicit proxy mode
  pending separate design. Use permitted direct egress, not environment bypass.
- Independently cap wire-entity/decompressed bodies at 8 MiB KEV / 2 MiB RSS;
  10,000 KEV / 500 feed items, UTF-8 only with optional BOM, depth 64, 32 KiB headers.
  No DTDs/custom entities/external resources. Invalid/empty envelopes and duplicate
  conflicting native IDs fail the whole batch. Empty valid RSS is not a retraction.
- Preserve metadata caps: title 512, URL 4,096, identifier/publisher 256 (URL GUIDs
  use URL cap), optional excerpt 65,536, other ingestion metadata 8,192 characters.
  Separate proposed full-body/derived aggregate/node/attribute budgets and exact
  safe transformation rules are in D024/[M1_EVIDENCE.md](M1_EVIDENCE.md). Reject
  oversized full text, never truncate or silently switch representation.
- HTML is inert, untrusted evidence. Sanitization never executes code, resolves
  resources or grants publication rights; original and transformed content stay
  distinct. No feed instructions can command the pipeline or an AI assistant.
- No credentials for selected public routes, malware execution, raw errors in
  logs or production fixtures. Keep source markings/private handling. Resolve
  D009 inheritance and authenticated review before any exporter.

## Costs and acceptance criteria

Software/open public routes are proposed at $0 license/API charges; paid-service
budget remains **$0**. Existing approved hardware still incurs electricity,
connectivity and operator time. No host is purchased or selected here. At one
cycle/day, about 90 primary GETs/month, ≤270 top-level attempts plus bounded
redirect/policy requests; body maxima imply ~360 MiB/month primary or ~1,080 MiB
with every attempt at cap, excluding headers/redirect/policy overhead. Stricter
source restrictions can reduce these maxima. Measure before operational approval.

| ID | Full-text acceptance requirement / tests (not yet met) |
| --- | --- |
| M1-AC1 | Three cleared source records with lawful full-text scope, approved policies/retention, B1 reconfirmation and B2 activation. Unresolved vendor rights or partial field content blocks completion; no metadata substitution. |
| M1-AC2 | Independently replaceable adapters and pure transforms; dependency tests prohibit adapter-to-storage/cross-adapter imports. Composition exception narrow and reviewed. |
| M1-AC3 | Round-trip all provenance and complete permitted source content; verify response/item/derived digests separately, date precision, transformation parents/versions and explicit availability. Original/sanitized/plain text never conflated. |
| M1-AC4 | Repeat/reorder/restart idempotency; original-content changes create immutable revisions even with identical sanitized output; A→B→A reuses available A; transform upgrades append derivations; no retraction inferred from RSS window. |
| M1-AC5 | Offline clocks prove one automatic cycle/24 hours, persisted retry budget, three-attempt maximum including recovery, Retry-After deferral, immediate 403 pause, publisher-stricter limits and source failure isolation. |
| M1-AC6 | SSRF/DNS/TLS/redirect/proxy tests plus safe XML/HTML encoding/entity/depth/size/mutation-XSS tests; no active tags/attributes/resources in sanitized output and no link fetched. Exact/over-limit cases fail safely. |
| M1-AC7 | Atomic source/derived artifacts and checkpoint rollback on crash/disk-full/transform failure; valid 304 requires all required backing; corruption, revocation, deletion, WAL/backup expiry and isolated restore tested. No bodies leak into logs/public artifacts. |
| M1-AC8 | V1 contracts/excerpt rules and report template unchanged; no AI analysis, attribution, Ghana claims or publication. Original analyst output only after later rights/review/TLP gates; private full text never public output. |
| M1-AC9 | Explicit capacity decision if rights/retention exceed 2 GiB; approved private-host/key/operator/backup checks and manual pilot before separately approved schedule. Stop/disable/recovery procedures verified. |
| M1-AC10 | Ruff/format/offline pytest on supported CI versions, only tracked F4 xfail; synthetic fixtures and current status/decision/handoff records. No documentation merge implies implementation approval. |

## Implementation sequence and stopping point

The [PR plan](M1_READINESS.md) keeps the approved M1-01 descriptors first, then
V2 full-text contracts, identities, SQLite/recovery, hardened transport, safe
parsing/transforms, independent adapters and manual offline integration. B1/B2
verification/activation and Gate C scheduling remain separately approved work.
The M1-01 implementation PR stops at offline descriptors/tests/documentation.
M1-02a is separately approved for data contracts and stops at its review PR.
See [delivery status](../STATUS.md); M1-02b onward needs fresh scoped approval. The full-text strategic target and acceptance criteria are unchanged.
