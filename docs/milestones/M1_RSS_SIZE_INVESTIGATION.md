# M1 RSS size investigation — Issue #10

Reviewed **2026-11-19**, against main `2ee82d4` (PR #13), M1 v1.3 and
the M1-02a contracts delivered by PR #9. **Documentation only; D027 proposed.**
[Issue #10](https://github.com/Ih4c/ghana-cti-pipeline/issues/10) remains open.
No publisher requests, new tests, cap/schema/dependency changes or operational
approvals result from this investigation. Unrelated implementation drafts are
outside this review. The [collection specification](M1_COLLECTION.md),
[evidence design](M1_EVIDENCE.md), [readiness sequence](M1_READINESS.md) and
[implemented contract reference](../M1_EVIDENCE_CONTRACTS.md) remain authoritative.

## Finding and evidence quality

There is insufficient evidence to say either vendor feed fits the current cap,
or to justify a larger cap. Retain existing contracts while obtaining separately
approved B1 measurements; keep sources disabled pending all applicable gates.
This is not a finding that 2 MiB is adequate for full-text collection.

Issue #10 records a **2026-11-18** one-off tool observation: approximately
1.63 million Google feed characters and 345 thousand Microsoft feed characters.
The tool truncated its view. These are neither complete response measurements
nor exact UTF-8 byte counts, and establish no byte headroom or compression ratio.
[Historical feasibility evidence](M1_SOURCE_FEASIBILITY.md) likewise distinguishes
tool output from runtime verification. No new source evidence was gathered here.

Unknowns include complete encoded/decoded sizes, compression and validators,
variation over time/request variants, item counts, largest and aggregate original
fields, actual full-text completeness, transformed sizes, peak memory, and lawful
access/processing/retention scope. Feed availability grants no redistribution right.

## Limit inventory: declarations versus runtime enforcement

Binary units: 1 MiB = 1,048,576 bytes; 2 MiB = 2,097,152 bytes;
8 MiB = 8,388,608 bytes. Exact maxima are inclusive.

| Layer | Existing limit | What main actually enforces |
| --- | --- | --- |
| Complete RSS transferred body | 2 MiB, independently of decoded size | `FeedFullTextEvidenceRevision` and feed-mode `ProcessingManifest` reject a declared count above the cap. No download counter exists. |
| Complete RSS decoded HTTP entity | 2 MiB, independently of transferred size | Same validators; response artifact count must equal declared decoded count. No decompressor or actual-byte check exists. |
| Generic receipt/response artifact | 0–8 MiB | `ResponseBodyMetadata` applies strict integer bounds separately to both counts; `ResponseArtifact` describes decoded bytes. A standalone receipt does not know the tighter RSS context. |
| Individual original feed HTML field | 1 byte–1 MiB UTF-8 | `OriginalHTMLArtifact.byte_count` is a strict bounded declaration, not an extraction or byte measurement. |
| Individual sanitized HTML / extracted plain text | Each 1 byte–1 MiB UTF-8 | Separate `SanitizedHTMLArtifact` and `PlainTextArtifact` declarations; no transformations exist. |
| Aggregate RSS original HTML / sanitized HTML / plain text | Each independently at most 2 MiB per source batch | Manifest sums byte counts of listed, uniquely identified artifacts by kind. This is not one shared 2 MiB allowance for all representations or for the response plus derivatives. |
| RSS item count / artifact references | At most 500 expected items; generic manifest list bounds 10,000 items/artifacts | Feed count check and complete-manifest item-count equality apply. Full-text associations require original, sanitized and plain-text backing; no metadata-only mode. RSS normally needs at most 1,500 item artifact references, excluding its response. |
| CISA comparison | 8 MiB transferred and decoded independently; 10,000 entries; each/aggregate catalog projection at most 8 MiB | Receipt, catalog context and manifest declarations enforce byte/count bounds; runtime measurement and parsing remain absent. |
| Headers / XML / HTML complexity | 32 KiB aggregate headers; UTF-8 with optional BOM; depth 64; no DTD/custom entities/external resources; 50,000 HTML nodes per batch; 32 input attributes per element, values at most 4,096 characters | Proposed runtime controls, not enforced by the artifact models. Selected receipt header values are individually capped at 1,024 characters; that is not an aggregate HTTP-header limit. |
| Ingestion metadata | Planned title 512, identifier/publisher 256, URL/URL GUID 4,096, optional excerpt 65,536, other metadata 8,192 characters | V2 identifiers/URLs/locators have explicit bounds, but generic V2 metadata (including title/publisher/native key) permits 8,192 characters. Tighter source mappings still need enforcement. V1 excerpt and `FetchedDocument.body` have no size cap. |
| Live storage / backup space | 2 GiB live store, warn at 80%; seven encrypted daily backups can add up to 14 GiB separately | Proposed operational accounting, not implemented. Include metadata/indexes/WAL and reserve temporary/free-space headroom; backup legality and deadlines remain unresolved. |
| Transfer / scheduling / cost | 512 MiB/day transfer; normally at most three attempts per source cycle; at most one cycle/source/24h after Gate C; $0 paid-service budget | Proposed runtime budgets only; redirects, retries and policy checks consume budgets too. No scheduler, storage or transport exists. B1 needs its own bounded manual request authorization. |

Implementation evidence: [retrieval.py](../../src/ghana_cti_pipeline/core/retrieval.py),
[artifacts.py](../../src/ghana_cti_pipeline/core/artifacts.py),
[evidence.py](../../src/ghana_cti_pipeline/core/evidence.py),
[processing.py](../../src/ghana_cti_pipeline/core/processing.py),
[evidence_values.py](../../src/ghana_cti_pipeline/core/evidence_values.py) and
[fetch interface](../../src/ghana_cti_pipeline/collectors/interfaces.py).
All are contracts/interfaces, not proof that measured bytes, retained content,
permission or completeness match supplied metadata. An incomplete manifest may
describe work in progress; it must not become a successful partial source batch.

## Measurement units

- **Transferred entity bytes:** encoded HTTP body octets before Content-Encoding
  decompression and after HTTP transfer framing is removed. Exclude TLS/TCP,
  headers and chunk framing from this body metric; record/account for ancillary
  traffic separately. This is not a claim to measure total network billing.
- **Decoded entity bytes:** the complete bounded decompressor output before
  UTF-8/XML parsing. Compression may make a large entity small on the wire;
  some encodings add overhead. Both limits must pass independently.
- **Content-Length:** an advertised length, usually of the encoded body, not a
  measurement or a bound on decoded size. Missing/chunked does not mean zero.
  Detect contradictory length/framing and premature EOF rather than accepting
  partial content. Record Content-Encoding, including identity/absence.
- **Original article-field bytes:** UTF-8 encoding of the complete field value
  produced by the safe XML parser (predefined XML entities/CDATA handled there),
  before HTML sanitization. Record parser/version and field namespace/selection.
  Do not add Unicode normalization, whitespace trimming or an HTML-unescape pass;
  XML parser normalization and the original response are distinct representations.
- **Characters are not bytes:** 2,097,152 ASCII characters, 1,048,576 `é` scalars,
  or 524,288 four-byte Unicode scalars each occupy 2 MiB in UTF-8. A viewer may
  count code units or display text rather than source characters. No conversion
  from the reported truncated view can establish the complete feed's byte size.

Original-field aggregate means the sum of complete selected field UTF-8 lengths,
not visible text or sanitized output. Future sanitizer serialization and extraction
separators can change sizes; measure their outputs independently in their approved
increment. Do not infer plain-text or sanitized sizes from original HTML.

## Proposed B1 procedure — not executed or authorized

### Preconditions and request budget

1. Obtain explicit source-specific B1 approval naming the measurement operator,
   approved runtime/network, tool versions, user-agent, exact HTTPS endpoints and
   allowed redirect hosts/paths, dates, request budget, caps, private output location
   and lawful transient processing/deletion basis. Robots compliance is necessary
   but not a license. Unresolved/prohibited access or handling pauses that source.
2. Candidate URLs, not activated endpoints: Microsoft
   `https://www.microsoft.com/en-us/security/blog/feed/` and Google
   `https://feeds.feedburner.com/threatintelligence/pvexyqv7v0v`.
   Review applicable publisher/intermediary terms and robots for the exact
   user-agent/path and every redirect host before following it. Do not infer that
   a root-path robots rule matches a different nested path. Terms/robots checks
   themselves require approved requests; record decisions and dated references.
3. Proposed sampling window: three manual samples per approved feed, at least
   24 hours apart over at least three days, subject to stricter publisher limits.
   For two feeds this is six primary GETs; explicitly budget policy requests and
   up to three redirect hops per GET separately. No automatic retries, HEAD
   probes, article requests, background timer or unapproved follow-up requests.
   A longer window may be needed to assess growth; three days cannot guarantee
   a future maximum. Owner approval must select actual dates and total requests.
4. Request the same explicitly recorded Accept-Encoding/user-agent variant on
   each sample. Full-body measurement needs an approved unconditional GET;
   record response validators without sending conditions for these samples.
   If a response is 304, record status/validators and any protocol anomaly, but
   mark current full-entity/item sizes unknown, not zero or reused as new data.
   Do not spend an extra unconditional request without authorization.

### Instrumentation and safety

5. Use an independently reviewed, offline-tested measurement harness; none is
   implemented by this PR. It must expose raw encoded body chunks rather than
   counting an HTTP client's silently decompressed stream as transferred bytes.
   Count encoded and decoded bytes independently while streaming; bound decoder
   output allocation before producing an oversized buffer. Require complete EOF,
   successful decoder integrity checks and valid framing for an exact measurement.
   Reject unsupported content codings, malformed streams and encoding conflicts.
6. Apply the existing transport design: HTTPS/443 allowlist, no credentials or IP
   literals; validate all A/AAAA as globally routable, reject special/metadata and
   IPv4-mapped IPv6 ranges, pin the validated IP with original-host SNI/certificate
   verification. Revalidate every hop; no automatic redirects/unchecked second
   DNS lookup. Disable inherited proxies; do not bypass environment restrictions
   or introduce explicit proxies. If approved direct egress is unavailable, stop.
7. Initially keep both RSS body ceilings at 2 MiB, headers at 32 KiB and existing
   deadlines (5s connect, 20s read, 60s attempt, 180s source, 10min run including
   parsing). Hops share source byte/time budgets; account per-hop bytes separately
   from the final response. No retry on size/parser/policy errors; 403 pauses,
   429 defers according to Retry-After, never forces a request within the window.
   The 512 MiB/day overall budget still applies and is not permission to spend it.
8. If a ceiling stops a stream, record a **censored measurement**: observed count,
   lower bound where known, stopping limit and incomplete status. Do not report
   the cap as the exact total or parse a prefix as a complete feed. The harness's
   bounded overflow-detection read/decoder allowance must be explicit in B1
   approval, including any one-byte probe. If a complete measurement needs higher
   diagnostic ceilings, obtain separate approval for those numeric ceilings and
   memory/time budget first. A diagnostic exception neither changes production
   contracts nor permits ingesting the oversized response as compliant evidence.
9. Only parse a complete, bounded entity with the approved safe XML parser:
   UTF-8/optional BOM, no DTD/custom entities/external resources, depth 64 and
   at most 500 items. Validate namespace and full-field selection (Microsoft
   `content:encoded`, Google `description`) rather than assuming it. Count each
   complete original field, maximum and aggregate UTF-8 bytes. Apply 1 MiB per
   field and 2 MiB aggregate; if a bound stops parsing, mark subsequent counts
   unknown/partial. A well-formed field is not proof of publisher article
   completeness; missing/summary-only/truncated fields block full-text acceptance.
   No article-page comparison request, rendering, remote resources, sanitizer or
   plain-text extractor is authorized by this measurement plan.
10. Process only in approved transient memory; do not archive the feed or fields.
    Prevent body dumps in exceptions, debug HTTP traces, temporary files, core
    dumps/swap and CI artifacts; use an approved host with suitable controls and
    discard buffers on success/failure. Save only bounded allowlisted measurement
    metadata in the approved private location. Never put vendor article bodies,
    titles or extracted text in GitHub issues, public logs, fixtures or artifacts.

### Measurement record (proposed worksheet, not a new contract)

| Group | Record |
| --- | --- |
| Provenance | Source ID, B1 approval reference, UTC start/end timestamp, harness/client/parser/runtime versions, request variant and effective limits, terms/robots decision references |
| HTTP | Requested feed URL, final validated URL and bounded redirect chain/statuses; final status; Content-Type, Content-Encoding, advertised Content-Length or absent/invalid flag; sent/returned ETag and Last-Modified |
| Bytes | Actual encoded/decoded counts per response and shared budget consumption; for each value mark exact, lower-bound or unknown; EOF/decoder completion, stop reason and overflow allowance consumed |
| Fields | Parsed item count, selected field name/namespace, largest complete field UTF-8 bytes and ordinal/locator, aggregate complete original-field UTF-8 bytes; missing fields and completeness/partial flags |
| Resources | Elapsed time, observed peak memory, ancillary request/transfer totals and remaining approved budget; no body excerpts |

Allowlist/bound all logged headers and reject control characters; never log cookies,
authorization headers or arbitrary response headers/errors. Record Content-Length
in this separate worksheet without extending M1-01's header schema. URLs must pass
the approved public-endpoint policy with no credentials or secret query values.
Zero, unknown and partial are different. A 304 can have no current body transfer
without establishing the current feed's full size. Later transformed HTML/plain-text
measurements need their own approved implementation; label them unmeasured here.

## Offline regression coverage: existing and proposed

No separate test-code authorization was given for this investigation; no tests
are added. Existing synthetic tests verify **declared** values:

- [test_processing_contracts.py](../../tests/test_processing_contracts.py):
  `test_rss_response_cap_in_manifest`, `test_aggregate_byte_limit_exact_and_above`
  and `test_item_count_exact_and_above` check exact maxima and rejection above;
  backing/contradiction tests reject missing full-text associations.
- [test_evidence_v2.py](../../tests/test_evidence_v2.py):
  `test_feed_evidence_enforces_response_cap` exercises both 2 MiB counters;
  `test_artifact_byte_boundaries` covers per-artifact bounds and strict integers;
  missing-backing/discriminator tests reject incomplete or metadata-only evidence.

Proposed separately authorized harness/transport/parser tests, using synthetic
payloads only and blocked external network access:

| Case | Required result |
| --- | --- |
| Exactly 2,097,152 bytes / one byte over, each counter independently | Exact-limit complete input accepted; oversized whole batch rejected; no truncated success, partial evidence or checkpoint advance |
| Tiny gzip transfer expanding to exactly 2 MiB / 2 MiB + 1 | Decoded counter controls acceptance independently; bounded allocation and overflow detection stop expansion before unbounded buffering |
| Encoded body over 2 MiB with decoded body below it | Transferred cap rejects even though decoded count would fit; compression is not a cap bypass |
| Same decoded entity, identity versus compressed transfer | Same decoded count, different measured transferred counts; neither inferred from Content-Length |
| Missing, misleading or conflicting Content-Length; malformed/truncated compression | Streaming counts remain authoritative; framing/integrity failures never become complete measurements |
| Multibyte Unicode, XML entities/CDATA and parser line endings | UTF-8 byte counts at exact/over boundaries, with no display-character counting or additional original-evidence normalization |
| Per-field 1 MiB / aggregate 2 MiB boundaries for each representation | Independent rejection; passing response size alone cannot make an oversized item/derivative valid |
| Missing/truncated field, DTD/entity/depth/item overflow, 304 | No silent field truncation, metadata fallback or false current-body completeness |
| Errors, cap stops and logging | Explicit partial/lower-bound metadata; synthetic body canaries never appear in logs/artifacts; no filesystem payload retention or external requests |

Actual-byte tests belong with the approved measurement harness and later M1-05,
M1-06a/M1-06b increments, not invented transport behavior inside data contracts.

## Decision matrix and recommendation

| Option | Security and memory | Storage and transfer | Full-text completeness / decision needed |
| --- | --- | --- | --- |
| Retain current 2 MiB response caps | Keeps present resource ceilings; runtime stream/decoder enforcement still needed; cap is not a RAM bound | Existing budget assumptions unchanged | May reject an entire growing feed indefinitely. Keep caps now, but do not assert measured suitability or activate on that basis. |
| Raise to a measured, justified value | Requires measured maxima, growth margin, peak-memory/decompression testing and explicit upper bounds | Recalculate snapshots, retries, retention, backups and daily transfer; larger response cap does not lift item/aggregate caps | Could admit complete feeds if all other bounds pass. Owner must approve exact independent caps and contract impact; no number is chosen here. |
| Source-specific caps | Limits additional exposure to the demonstrated source; adds policy/configuration and validation complexity | Attribute growth and budgets to that source; retain shared daily/store ceilings | Useful only with evidence. Lower runtime caps can fit existing hard maxima; raising a source above 2 MiB still requires approved contract changes, not a configuration bypass. |
| Defer affected source | Avoids its unverified processing/memory exposure | No collection/storage traffic for that source | No full-text coverage from it. Three-source completion stays unmet unless owner explicitly revises scope. Appropriate while rights or size feasibility remain unresolved. |

Recommendation: **leave caps unchanged and sources disabled, then seek a bounded
B1 measurement approval**. Choose any production cap only after reviewing dated
byte measurements over time, full-field completeness and all other limits. The
generic 8 MiB receipt ceiling is not permission to use it for RSS; exceeding it
would additionally require explicit generic-contract/schema compatibility review.

At current maxima, one daily snapshot set is 12 MiB; CISA projections add 8 MiB
and three representations for each of two feeds add 12 MiB: **32 MiB/day before
overhead**, approximately 11.4 GiB/year. A 2 GiB store holds fewer than 64 such
days after overhead. Raising only one response cap by Δ MiB adds up to Δ MiB/day
of snapshots; raising that response plus all three aggregate caps by Δ adds up
to 4Δ MiB/day. Retries increase transfer without necessarily adding retained data.
Compression saves transferred bytes, not decoded storage or parser memory.
Simultaneous buffers, Unicode strings, DOM nodes and derived outputs mean peak RAM
can greatly exceed the entity cap. Measure it; do not equate 2 MiB with RAM use.
No deduplication, retention deadline, hosting purchase or larger budget is assumed.

## Owner decisions and Issue #10 completion

1. Separately authorize any synthetic measurement-harness/test implementation,
   including tool/dependency choices; this PR supplies a test plan only.
2. Approve B1 per source with lawful transient handling, exact endpoints/redirects,
   approved egress/runtime, dates/frequency/total request budget, instrumentation,
   numeric ceilings/overflow allowance and private metadata handling. An initial
   cap-stopped sample may require a further bounded diagnostic approval.
3. After measurements, select and record the cap policy/headroom with explicit
   transferred, decoded, per-item and aggregate limits; assess compatibility,
   memory, storage/retention/backups and transfer budgets. Approve any resulting
   contract/test changes separately. D027 remains proposed until this decision.

Issue #10 stays open until its measured, multi-day byte evidence and owner-recorded
decision are supplied. Include complete versus censored results, all relevant
request variants/limits and remaining uncertainty; a plan alone does not satisfy
its follow-up. Any approved cap change needs regression validation. Choosing
deferral without those measurements requires an explicit owner revision of the
issue's acceptance scope, not automatic closure. B2 activation and C recurring
scheduling remain separate approvals; this task authorizes neither.
