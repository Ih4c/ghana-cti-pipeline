# M1-02a full-text evidence contracts

Implementation under M1 v1.3, delivered by PR #9. The
[owner approval on PR #8](https://github.com/Ih4c/ghana-cti-pipeline/pull/8#issuecomment-6997113844)
covers D019/D024 data-only evidence, artifact-reference, provenance, source-policy
and processing-manifest contracts, synthetic tests and documentation.
[M1_EVIDENCE.md](milestones/M1_EVIDENCE.md) supplies the strategic requirements;
[STATUS.md](STATUS.md) separates delivered work from this implementation branch.

The separately [approved D027 amendment](https://github.com/Ih4c/ghana-cti-pipeline/issues/10#issuecomment-7008185129)
raises RSS response and each representation aggregate from 2 MiB to 6 MiB under
v1.3. The 1 MiB per-article and generic 8 MiB ceilings, schemas and serialized
shapes are unchanged. This widens accepted declared counts only; runtime byte
measurement remains unimplemented, and B1 must still establish actual headroom.

## Modules and schemas

| Module | Responsibility |
| --- | --- |
| [evidence_values.py](../src/ghana_cti_pipeline/core/evidence_values.py) | Strict bounded values, calendar dates/aware timestamps, inert reference URLs, policy references and validated immutable base |
| [artifacts.py](../src/ghana_cti_pipeline/core/artifacts.py) | Discriminated artifact references, parent/digest relationships, transformation descriptors and separate availability assertions |
| [evidence.py](../src/ghana_cti_pipeline/core/evidence.py) | EvidenceRevisionV2 union, two source modes, original-field projection, provenance/publication precision and receipt/reference consistency |
| [source_policy.py](../src/ghana_cti_pipeline/core/source_policy.py) | Declared processing/representation scope, basis metadata and per-class deadlines; no authorization enforcement |
| [processing.py](../src/ghana_cti_pipeline/core/processing.py) | Manifest item references, completeness, bounded associations and supplied artifact-graph validation; no transactions/checkpoints |

Every model inherits frozen, extra-forbid validation and revalidated shallow/deep
copy updates. Nested new models revalidate supplied instances. Use validated
construction/JSON ingestion, never unchecked `model_construct` at trust boundaries.
These data models generate no ID, timestamp, digest or source content; the
separately approved M1-02b pure helpers return explicit computed values. Helper/descriptor schemas
are `1.0`; the two evidence modes are `2.0`, with `kind: hybrid`, compatible with
M1-01 observations. Required `mode` discriminates `EvidenceRevisionV2`; use Pydantic
`TypeAdapter(EvidenceRevisionV2)` for union ingestion. Existing V1/M1-01 code and
serialized representations are unchanged.

## Evidence and provenance

Both evidence variants require caller-supplied UUID `evidence_id`, `logical_item_id`,
`metadata_digest`, `provenance` and a complete response artifact reference.
`confidence` is fixed to `unknown`; `tlp` defaults to null and can only carry an
explicit caller-supplied marking. There are no Ghana relevance/attribution fields.

`EvidenceProvenance` requires source ID, publisher and supplied/configured origin;
optional byline requires an origin too. The source key is a discriminated
`native_id` or exact `original_url` fallback. It carries the original article URL
separately from `first_acquisition`, an unchanged M1-01 ReceivedResponse (HTTP 200),
plus request-variant ID, locator, adapter/parser versions, identity profile and
source-policy reference. Source IDs must agree; URL fallbacks match exactly.
Receipt status/times/redirects/header allowlisting retain M1-01 validation.

`PublicationDate` preserves supplied text (including an invalid empty string),
precision `unknown/date/timestamp`, and parse outcome `missing/invalid/parsed`.
Unknown values carry no parsed date/time; missing means absent text, invalid means
supplied text without a parsed value. Parsed records require text and exactly the
value matching their precision. Calendar dates accept date objects or YYYY-MM-DD;
timestamps require an explicit offset. These validators do not parse feed dates,
guess time zones or verify that arbitrary publisher text was interpreted correctly.

- `catalog_entry`: `CatalogContext` (title, catalog version, release timestamp,
  count 1–10,000), `CatalogFields` and `entry` artifact. The typed known-field
  projection preserves cveID, vendorProject, product, vulnerabilityName, dateAdded,
  shortDescription, requiredAction, dueDate, knownRansomwareCampaignUse, notes and
  cwes. The complete original structured entry remains an artifact, including any
  future source extensions. Native key must equal cveID; field/entry locators agree.
  dateAdded/dueDate are catalog dates, never inferred publication dates. The original
  advisory URL may be absent; no URL is invented. Adapter mapping is still future work.
- `feed_full_text`: title, required original article URL and all three required
  references: `original`, `sanitized`, `plain_text`. Original source field is
  `content:encoded` or `description`; no metadata/summary-only mode. The original
  locator matches provenance. Transferred and decoded RSS receipt counts each cap
  at 6 MiB. Models contain no article HTML/plain-text payloads.

## Artifact and digest descriptors

Each artifact has UUID `artifact_id`, kind, SHA-256 descriptor, digest domain,
strict `byte_count` and policy reference (source ID/policy ID/version). Response
artifacts name their retrieval UUID; byte count and any computed M1-01 receipt
digest must agree. A receipt with not_computed digest can acquire a separately
supplied artifact digest; no computation happens here.

| Artifact kind | Digest domain | Parent / processing metadata | Byte cap |
| --- | --- | --- | --- |
| http_response | decoded-http-entity-v1 | None; required retrieval ID | 0–8 MiB; RSS receipt/manifest applies 6 MiB |
| original_html | feed-field-html-utf8-v1 | HTTP response; field locator/source field | 1 byte–1 MiB |
| sanitized_html | sanitized-html-utf8-v1 | Original HTML; sanitize_html transformation | 1 byte–1 MiB |
| plain_text | plain-text-utf8-v1 | Sanitized HTML; extract_text transformation | 1 byte–1 MiB |
| catalog_entry | catalog-entry-json-v1 | HTTP response; entry locator | 1 byte–8 MiB; aggregate also capped |

`ArtifactReference` discriminates on kind. Parent references include UUID, kind,
digest and domain; transformation descriptors carry operation, implementation
version, parser version and configuration SHA-256. Supplied graphs reject missing
parents, mismatched kind/domain/digest, self/duplicate IDs and different policies.
Graph topology is response → original → sanitized → plain, or response → entry.
Model hashes are declared exactly 64 lowercase hex characters; model validation
does not calculate them or compare them with actual bytes. Artifact IDs are association references, not a
claim that identical hashes share permission or acquisition history.

`EvidenceMetadataDigest` uses `evidence-metadata-json-v1`;
`ManifestDigest` uses `processing-manifest-json-v1`. These and the derived/catalog
domain labels are the existing wire choices (D025). Separately approved M1-02b
[profiles and helpers](M1_IDENTITY_PROFILES.md) implement canonical field projections
and hashing, exclude self-digests and keep source/derivation identities distinct.

`ArtifactAvailability` is a separate dated record: artifact/policy reference,
state `available/expired/deleted/unavailable`, recorded_at and retention_until.
An available assertion must precede expiry; expired cannot precede its deadline.
Historical evidence stays immutable when availability changes. No lookup, current
clock, erasure verification, ledger update or perpetual availability is implied.

## Policy and manifest rules

`SourcePolicy` records reference, endpoint, mode, operator/purpose, basis status,
references/review date, permitted artifact kinds and processing scopes, conditions,
effective/expiry timestamps and retention deadlines. Basis defaults to `unresolved`;
`documented` requires references/date, not verified publisher permission. Modes
cannot declare the other mode's artifacts or catalog HTML transformations. Scope
entries are unique; allowed operations are retrieve/retain/sanitize_html/extract_text/
internal_use/backup, with no publish operation. Conditions preserve declared access,
sharing, quotas and backup/deletion requirements without executing them.

`RetentionDeadlines` requires aware deadlines for response, original, derived,
metadata, digests, audit and backups. Deadlines cannot precede the policy effective
time. Policy validity and retention deadlines are distinct: expiration pauses use
under future enforcement, and cannot be treated as permission to retain or restore.
There is no indefinite-retention default or automatic renewal.

`ProcessingManifest` records UUID, mode/policy, a 200 retrieval, request variant,
adapter/parser/profile versions, expected count, complete/incomplete state, response,
items/artifacts and a manifest digest. Each item names evidence UUID/kind/version
and metadata digest, locator and required artifact IDs for its mode. Complete
requires the declared item count to match; incomplete permits a partial set. Empty
feeds/catalogs can have a complete zero-item manifest but produce no evidence.

All listed artifacts must be associated, policies agree, IDs/locators are unique,
and every supplied parent link resolves with matching digest/kind. Catalog entry
artifacts total ≤8 MiB; each vendor representation totals ≤6 MiB independently.
Counts cap at 10,000 catalog items or 500 RSS items. Manifest artifact lists cap at
10,000 (catalog maximum; RSS needs at most 1,500), excluding the one response.
These local checks do not resolve evidence IDs against a repository, verify payload
completeness or make a manifest eligible for a conditional checkpoint.

## Bounds and implementation choices for review

Source/policy/request IDs: 1–256 nonblank strict characters; versions/profile IDs:
1–128; locators/reference URLs: 1–4,096; general metadata/native keys: 1–8,192.
Publication source text and catalog notes permit empty strings, max 8,192.
All strings preserve input; no truncation/coercion. Inert reference URLs allow
HTTP(S) and fragments, forbid credentials, whitespace/control characters and
malformed escapes; transport URLs keep unchanged stricter M1-01 HTTPS rules.
Neither form performs DNS or SSRF checks.

D025 records wire-level details absent from the prose specification: named domain
labels, known KEV field projection, maximum 128 CWE values/32 policy references,
nonempty item-artifact byte assertions, and required finite policy deadlines.
They were delivered by PR #9 and are not claims that runtime source feasibility has
been measured. If an article yields an empty derivative, this contract cannot
claim full-text completion; transformation behavior remains a later decision.

D026 is resolved for M1-02b by the [identity profile](M1_IDENTITY_PROFILES.md):
`evidence_id` identifies original source content, while a separately computed
evidence-association UUID identifies the full immutable bundle. Derived identities
bind output, transform versions/configuration and immutable parents. A manifest
item selects an association using evidence ID plus metadata digest. Never overwrite
a bundle keyed only by evidence_id; M1-03 enforces those storage keys. Existing
wire fields and versions remain unchanged, including D027 and per-article limits.

## Validation and exclusions

[Synthetic fixtures](../tests/fixtures/evidence_v2.json) cover CISA, Microsoft and
Google shapes with invented IDs/digests/metadata. Tests exercise missing backing,
contradictory provenance/derivations, exact and excessive byte/count/text limits,
date precision, policy/availability metadata, nested/shallow/deep copy validation,
compatibility and blocked network. See [STATUS.md](STATUS.md) for results.

M1-02b adds [digests.py](../src/ghana_cti_pipeline/core/digests.py) and
[identities.py](../src/ghana_cti_pipeline/core/identities.py), with synthetic
[golden vectors](../tests/fixtures/identity_vectors.json) and tests. The separately
approved [M1-03 store](M1_SQLITE_STORAGE.md) persists these unchanged contracts,
rechecks actual BLOB lengths/hashes and guards conditional checkpoints using
complete policy/manifest/observation backing. It introduces no core wire changes.
There is no networking, source access, feed parsing, sanitization, adapters,
scheduling, deployment or reporting change. Validation
errors may include rejected input; future logging must use safe codes, not raw
ValidationError payloads. Rights and operational approval gates remain unchanged.
