# M1 full-text evidence, permissions and retention design

Design **1.1**, 2026-11-19; companion to [M1 v1.3](M1_COLLECTION.md).
D022 accepts full-text collection as the strategic target, superseding D018's
metadata-first vendor target. D023 records owner-reported terms findings and risk
acceptance, not legal clearance. M1-01 and M1-02a data contracts have
[scoped approvals](../DECISIONS.md); the remaining technical design stays proposed.
The [contract reference](../M1_EVIDENCE_CONTRACTS.md) records implementation wire
choices (D025) and [resolved identity/association profiles](../M1_IDENTITY_PROFILES.md)
(D026), implemented by separately approved M1-02b pure helpers. No source
requests, terms lookups or live verification were performed for this revision.

D027 is a separately [approved numeric-cap amendment](../DECISIONS.md) under
M1 v1.3: RSS responses and each representation aggregate rise from 2 to 6 MiB;
1 MiB per article and 8 MiB generic ceilings remain. No schema redesign or source
access is approved. The resulting capacity bounds below are calculations, not
measured feed sizes; B1 still needs to confirm headroom.

## Source coverage and rights gates

| Source | Required source content | Evidence basis and unresolved activation conditions |
| --- | --- | --- |
| CISA KEV | Complete permitted catalog entries, original fields and provenance | Historical catalog/schema/CC0 checks remain in the feasibility log. Reconfirm endpoint/access policy and license scope before activation; linked third-party material, logos and endorsement are not covered. |
| Microsoft Security Blog RSS | Complete article HTML supplied in RSS `content:encoded` | Owner reports observing this structure on 2026-11-18. Independently reconfirm field, namespace, completeness and limits during approved B1. Owner reports copying/distribution/publication restrictions and possible use limits; lawful collection, transformations, private retention and backups remain unresolved. |
| Google Threat Intelligence/Mandiant RSS | Complete article HTML supplied in RSS `description` | Owner reports observing this structure on 2026-11-18. Independently reconfirm completeness and limits during approved B1. Applicable Google/service/regional terms and FeedBurner/redirect-host robots/access requirements must be reviewed; lawful collection/retention remains unresolved. |

These vendor field observations are **owner-supplied**, not newly verified runtime
findings. A populated field or accessible feed does not prove a complete article
or permission to retain it. Missing/truncated required content fails full-text
acceptance; block the source and seek a scope/permission resolution. Do not replace
it with metadata-only collection, follow article links, backfill historical pages,
or buy API access. A permitted CISA-only pilot is not three-source M1 completion.

The owner accepts the identified operational/legal risk of the proposed private
research workflow. This is not a license, copyright exception, legal conclusion,
or permission to ignore terms/robots/access restrictions. Prohibited full-text use,
or a mode without an established lawful basis, cannot be activated merely because
it is technically possible. Commercial use or public republication requires a
separate permissions review and any necessary written authorization.

Before B1, document a lawful basis for its exact bounded access/processing scope;
before B2, clear the proposed persistent full-text workflow. Open questions are:

- Which operator/entity, jurisdiction and research purpose do the applicable terms
  cover? Do automated feed access, internal copying and retention have permission?
- Does that basis cover complete feed responses, embedded articles/third-party
  content, sanitization/plain-text derivation, internal analysis and backups?
- What attribution, access controls, user-agent, frequency, robots, deletion,
  revocation and maximum-retention conditions apply to each representation?
- What separate restrictions govern short quotations, extracted facts/IOCs/TTPs,
  original analysis, external sharing, commercial use and public publication?

Possible routes are explicit written publisher authorization, an applicable
license grant covering the intended uses, or other legally supported grounds
assessed for the actual circumstances. Record the supporting scope and reasoning;
do not presume an exception or treat risk acceptance as that assessment. If the
basis cannot be established, mark full-text activation **blocked**. A terms
conflict is not resolved by slower polling or calling the store private.

Each versioned source policy records exact endpoints, operator/purpose, terms and
permission references/review date, authorized processing/representations/uses,
per-class deadlines, transformations, backup/deletion conditions, access/sharing
restrictions, user-agent/quotas and approval/expiry. Policy IDs/versions accompany
acquisitions and observations. Endpoint availability is separate from rights.

## Representation and provenance (D019/D024)

Keep V1 SourceItem/EvidenceRecord, their required nonblank excerpt and exact
excerpt hash, and Collector/FetchedDocument/EvidenceRepository unchanged. M1-02a
implements additive `EvidenceRevisionV2` data contracts, delivered by PR #9; never silently reinterpret V1 schema 1.0 or
stuff a full article into its excerpt. M1-01 remains data-only retrieval/observation
descriptors with no body bytes or retention claim; V2 is outside that increment.

V2 target modes are `catalog_entry` and `feed_full_text`, both backed by permitted
retained source representations. Metadata-only is no longer a target completion
mode. Any future legacy metadata record must keep its historical limitations;
never relabel a hash/reference as a retained full article.

| Provenance group | Required meaning |
| --- | --- |
| Source | Configured source ID, publisher/byline as supplied or configured with origin identified, GUID/native ID or explicitly typed exact original-URL fallback |
| URLs | Configured feed/catalog URL, actual final URL and redirects, original article/advisory URL retained separately; no guessed URL or automatic link following |
| Dates | Supplied publication text, precision `unknown/date/timestamp`, date or aware timestamp only where justified; missing/invalid dates remain unknown with parse outcome. Separate retrieval start/end timestamps; CISA dateAdded/dueDate remain catalog dates, not publication/targeting claims. |
| HTTP | Retrieval ID, status, sent/returned ETag/Last-Modified, permitted cache headers and fixed request-variant identity; allowlisted bounded fields only, no credentials/cookies/raw header dump |
| Versions/policy | Adapter, parser, evidence schema, identity profile and transformation versions/configuration IDs; source-policy ID/version and rights basis; first acquisition and later observation links |
| Integrity/history | Separate response, original item, sanitized and plain-text hashes; logical item and immutable revision IDs; explicit derivation parents/locators and chronological observations |
| Availability | Original/derived artifact association, retention deadline and current `available/expired/deleted/unavailable` state resolved through a separate lifecycle ledger; historical association does not promise perpetual availability |
| Analytical limits | Confidence unknown and TLP null unless supplied; no automatic credibility, attribution or Ghana targeting. All content remains untrusted and private. |

For each authorized vendor article retain three associated representations:

1. **Original article HTML:** the complete selected XML field's decoded character
   content, serialized to UTF-8, before HTML parsing/sanitization. Preserve the
   complete response separately with an item/field locator. XML line-ending/entity
   decoding means this is not a byte-for-byte substring of the HTTP response.
2. **Sanitized HTML:** a separately stored deterministic transformation with parent
   original-body digest, sanitizer/parser version, policy/configuration digest and
   its own output hash. Never overwrite the original or call sanitized text exact.
3. **Plain text:** a separately stored deterministic extraction from sanitized HTML,
   with that parent's digest, extraction version/configuration and independent hash.
   Preserve meaning; normalization is declared, not an analyst summary or new fact.

The complete HTTP entity is retained after Content-Encoding decoding and before
character/XML/JSON decoding, hashed in domain `decoded-http-entity-v1`; it is not
a wire-byte hash. Original HTML uses domain `feed-field-html-utf8-v1`; sanitized
and plain-text outputs use distinct versioned UTF-8 domains. Canonical retained
metadata/manifest digests are separate again. A digest proves integrity against a
known record, not publisher authenticity, legal rights or truth. A digest without
bytes cannot reproduce missing content. Weak ETags are opaque cache validators.

CISA retains the complete catalog response plus original structured entry fields
and locators. Its entry projection has a versioned canonical JSON digest, not an
invented HTML body. The vendor three-representation transformation requirement does
not force CISA into HTML. Original values, source context and date precision survive.

## Safe parsing and transformations (D008/D015/D024)

All transformations are proposed deterministic source processing, not AI analysis.
Use maintained, pinned open-source XML/HTML parsing and sanitization components,
selected in a separately reviewed implementation. Do not use regex as an HTML
sanitizer or run a browser. Existing XML rules stay: UTF-8 only (optional BOM),
reject conflicting/unsupported encoding declarations, DTDs, custom entities and
external resources; predefined XML entities/CDATA are decoded by the safe parser.
Preserve original bytes so decoding/normalization is auditable. No double-unescape
pass after sanitization. Invalid or over-budget source batches fail atomically.

Proposed HTML policy: allow inert structural tags only (`p`, `br`, headings,
lists, blockquote, pre/code, strong/em and basic table structure); remove all
attributes, including event handlers, styles, IDs and resource-bearing URLs.
Unwrap anchors to visible text; retain original article URL only as provenance.
Drop script/style, iframe/object/embed, forms/controls, media/image, SVG/MathML,
base/meta/link elements and their active subtrees, comments and processing
instructions. Unknown inert wrappers may be unwrapped after safe parsing.
Define/test exact allowlist and serialization in the approved sanitizer PR.
Never execute HTML, load remote fonts/images/scripts, resolve embedded links,
or treat sanitization as permission to publish or a complete viewer security model.

Plain-text extraction walks the sanitized tree: preserve text order and Unicode;
use explicit versioned separators for paragraphs/lists/line breaks/table cells,
normalize line endings deterministically, and record those transformations.
No paraphrasing, IOC enrichment, attribution or Ghana relevance generation.
Original HTML is never rendered directly. A future analyst viewer needs separate
review and output escaping/isolation; no viewer is introduced by M1.

Keep complete response caps: 8 MiB KEV and 6 MiB per RSS, independently enforced
on transferred and decompressed entity bytes; 10,000 KEV/500 RSS items; depth 64,
32 KiB headers, existing metadata/URL limits. D024 additionally **proposes**:
1 MiB UTF-8 per vendor original/sanitized/plain-text item, 6 MiB aggregate per
representation per vendor response, 50,000 HTML nodes per source batch, depth 64
and 32 input attributes per element with values ≤4,096 characters. CISA retained
entry projections total ≤8 MiB per catalog. These are bounds, not measured feed
sizes or automatic permission to raise limits. Processing shares the source/run
deadline; exceeding any cap rejects the batch, never truncates full-text evidence.
The old 65,536-character excerpt limit remains for optional short excerpt fields;
it is not silently reused as a full-article limit. General 8,192-character metadata
limits do not apply to the separately bounded full-text artifacts.

## Identity, atomic commits and conditional requests (D012/D013/D019)

Logical keys use source ID, native-key-kind and exact GUID/native ID or original
URL fallback. [M1-02b profiles](../M1_IDENTITY_PROFILES.md) fix namespaces,
canonical JSON and golden vectors. Source revisions depend on original content
and explicit supplied feed metadata/publication text, excluding parsed date
interpretations, typed catalog projections, retrieval time, item order and
catalog release metadata. Complete original catalog entry digests cover source
fields and extensions; parsed publication precision remains association metadata. Reordered feed items do not change item identity.
A→B→A reuses still-available A and adds an observation, without mutable predecessor
links. A changed original article creates a revision even if sanitization yields
the same text. Transform version/configuration changes create new immutable
**derived** artifacts linked to the same original revision, not rewritten history.
Policy renewals alone do not fabricate content changes; revoked/deleted material
cannot be resurrected without a reviewed lawful re-acquisition/identity rule.

A complete successful source transaction commits the permitted response artifact,
original item revisions, required derived artifacts and associations, retrieval,
observations, policy references, a manifest with item/artifact digests and all
processing versions, and the conditional checkpoint. Validate/transform before
opening the transaction; no network I/O while holding it. A required transformation
failure rolls back the whole source batch; other sources continue. Failure events
contain safe codes/counts only and never advance the successful checkpoint.

An eligible conditional checkpoint requires the fully processed committed 200,
intact manifest, available original response/item backing and required derived
artifacts, current rights and matching endpoint/request/processing profile.
Valid 304s refer directly to that 200, never another 304; update check time and
returned validators only, with no new item observation/body hash/publication date.
They do not prove article truth or byte equality independently checked by us.

- Missing/corrupt required state invalidates the checkpoint. Repair derived output
  from intact permitted originals locally under a reviewed transform version;
  otherwise one unconditional recovery fetch may consume a remaining attempt in
  the same cycle. Rights must still permit it; no budget means defer to next cycle.
- Changed parser/sanitizer/profile requires reviewed reprocessing of retained
  originals and a newly validated manifest before reusing conditional state. No
  fabricated network observation and no mutation of prior processing history.
- Rights expiry/revocation pauses the source and invalidates affected checkpoints;
  no automatic re-fetch to restore deleted material or extend rights on a 304.
- Unsolicited 304, changed redirect representation or mismatched source/validators
  fails; never forward old conditionals to a different representation. Unsupported
  Vary (including `*`) disables conditionals; unsupported no-store restrictions
  pause for policy review. HTTP cache metadata is not a license.

The v1.2 metadata-only 304 exception is no longer the target collection rule.
No source becomes complete merely because metadata or a response hash survives.

## Storage, capacity and lifecycle (D005/D013/D017/D020)

Propose one private SQLite database with foreign keys, typed artifact modes,
policy-aware associations and content-addressed BLOBs for bounded response,
original and derived artifacts. Shared digests do not share rights or extend
retention. BLOBs simplify atomic commits and crash recovery but enlarge the DB,
WAL, backups and purge work. Separate files could improve streaming/large-object
management but require atomic staging, reference commits, orphan cleanup and
coordinated backup/deletion. Defer that alternative until measured need and an
explicit reviewed decision; no silent external-artifact backend or cap increase.

Keep the **2 GiB live-store cap** (warn at 80%), single writer/run and $0 incremental
paid-service budget. Capacity accounting must include DB/WAL/temporary processing
headroom; pause before writes cannot fit, not after exhausting the disk. At daily
response caps, snapshots alone total 20 MiB/day (~7.13 GiB/year). With up to 8 MiB
CISA entry projections plus three 6 MiB vendor representations per feed, the
planning upper bound is **64 MiB/day (~22.8 GiB/year)** before metadata/indexes/WAL.
A 2 GiB cap holds fewer than 32 such days after overhead; deduplication may help,
but no retention guarantee follows. These are worst-case budget calculations,
not measured source sizes. Measure an authorized pilot; resolve capacity/retention
explicitly before activation. No automatic storage purchase or increase.

Store outside Git, web roots, public sync, CI artifacts/caches and PR attachments,
under an approved least-privilege account with owner-only paths and encryption at
rest; SQLite is not encrypted by default. Originals and derivatives are equally
private. No bodies/HTML, snippets, titles or raw validation exceptions in logs,
traces or crash dumps. Use safe error codes/counts/structural locators. Synthetic
fixtures only, never record real feeds. Host swap/dump/temp-file and backup controls
need operator verification; memory encryption alone does not grant retention rights.

Before B2, specify source-specific maximum retention for response/original/derived
bodies, metadata, digests, audit records and backups. The former 365-day reporting
target is a planning aspiration subject to rights/capacity, not a minimum right to
retain data. Seven encrypted daily backups may require up to 14 GiB separately;
expiry may shorten restore-point history. Approve operator, key handling, storage
and restore/purge procedure. A rights change pauses collection, identifies affected
originals/derivatives/associations, invalidates checkpoints and enforces deletion
within the required deadline. Do not preserve derivatives as a loophole.

Inventory live rows/indexes, free pages, journals/WAL, temporary files, replicas
and every backup. SQLite DELETE alone is not verified erasure: test a practical
purge/compaction/WAL and backup retirement/replacement procedure before activation.
If deadlines cannot be met, block onboarding. Retain only independently permitted
opaque tombstones/digests; mark citations unavailable. Restore in isolation using
the current rights/deletion ledger before serving data or enabling checkpoints.
Use consistent SQLite backups, not blind live-file copies; verify artifact hashes,
derivation links, manifest completeness, foreign keys and schema versions. Test
crash/disk-full rollback and idempotent operation retries; same ID/different content
rejects. Do not blindly downgrade newer schemas or silently purge cited evidence
for space. Mandatory deletion still takes precedence over retention aspirations.

## Reporting compatibility and limits (D009/D021/D022/D023)

The existing Ghana CTI template remains authoritative and unchanged. Its reference
in [REPORTING_STANDARDS.md](../REPORTING_STANDARDS.md) is present, but the template
artifact is not in this checkout. Version/license and field-level tooling review
remain open. Microsoft research is an optional analytical-quality reference, not
a replacement template. No report generator, viewer or publisher is implemented.

Permitted full-text evidence improves reproducibility: analysts can inspect exact
retained source fields, transformations, dates, citations and revisions. It does
not validate publisher claims, turn feed retrieval into independent article-page
verification, or establish Ghana targeting. Missing/truncated bodies and deleted
backing remain explicit gaps; sanitization/text extraction may omit meaningful
structure, so analysts must be able to compare with the private original safely.

Future public output is original analyst-written assessments, supported technical
findings, relevant facts/IOCs/techniques, qualified Ghana relevance and actionable
defensive recommendations, with source names, original URLs and publication dates.
Only short attributed quotations where legally permitted; no full articles,
extensive vendor excerpts, raw HTML or private snapshots. Facts/indicators/
techniques remain subject to applicable rights, confidentiality, source terms and
publication restrictions, not presumed universally unrestricted. Commercial use
or republication has its own permissions review. Retention permission does not
authorize publication. Human final judgment, authenticated review, evidence/TLP
inheritance, exact-revision approval and TLP:CLEAR remain required before export.
AI remains limited to permitted Stage 1/2 assistance; this M1 design adds no AI.
