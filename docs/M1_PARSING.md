# M1-06a pure source parsing

Implementation under M1 v1.3 / D015 and the safe-parsing portion of D024.
The [owner approval on PR #19](https://github.com/Ih4c/ghana-cti-pipeline/pull/19#issuecomment-7138988824)
was verified before application changes. PR #19 merged at `170ab1a`, verified
2026-11-24. D031 records the concrete profile below for independent review.
No source mapping, HTML transformation or operational gate is approved here.

## API and boundaries

- [rss_parser.py](../src/ghana_cti_pipeline/collectors/rss_parser.py):
  `parse_rss(raw, *, body_namespace, body_local_name) -> RSSBatch`.
- [catalog_parser.py](../src/ghana_cti_pipeline/collectors/catalog_parser.py):
  `parse_catalog(raw, *, entries_field, native_id_field) -> CatalogBatch`.
- [parsing_values.py](../src/ghana_cti_pipeline/collectors/parsing_values.py):
  shared bounds, safe `ParseError` codes and small extraction result types.

Both require complete decoded HTTP entity **bytes**, not strings, file objects,
paths, URLs, compressed input or transport descriptors. Pure functions have no
storage/transport imports, network, filesystem, clock, randomness, logging or
callbacks. The caller retains the original input separately; no parser result
claims retention, rights, authenticity or a successfully committed source batch.
Parser profile/version is `m1-safe-parsing-v1`, distinct from unchanged wire schemas.

The functions return only after the whole envelope validates. Failure exposes a
finite `ParseError.code`; never log exception internals/locals, source text or
returned containers. Results suppress content in their default repr. RSS results
use frozen dataclasses/tuples; JSON results contain fresh ordinary mutable JSON
containers (the entries tuple refers to objects in `document`). They are transient
extraction results, not new persisted contracts or validated evidence models.

## RSS 2.0 profile

Use standard-library `xml.parsers.expat`, with explicit UTF-8 and expanded
namespace names. Strict UTF-8 validation precedes XML parsing; one optional BOM is
accepted. XML declarations must say version 1.0 and, if supplied, UTF-8
(case-insensitive). Unsupported/conflicting declarations and malformed XML fail.
DTD declarations, internal/parameter/custom entities, external entity handling,
processing instructions (including stylesheets) and XInclude elements reject.
No external-resource resolver is installed; predefined entities, character
references and CDATA are decoded once by Expat. Comments are ignored.

Require an unnamespaced `rss` root with `version="2.0"`, exactly one direct
`channel`, and nonblank channel `title`, `link` and `description`. Items must be
direct channel children. A valid zero-item channel returns an empty tuple;
this never represents deletion or retraction. Do not infer absent item metadata.

Extract direct item fields without stripping, Unicode normalization, date parsing,
URL rewriting or precedence selection:

| Expanded field name | Bound in Unicode characters |
| --- | --- |
| RSS `title` | 512 |
| RSS `link` | 4,096 |
| RSS `guid` | 256, or 4,096 for HTTP(S)-prefixed values |
| RSS `author`, `source`; Dublin Core `creator`, `publisher` | 256 |
| RSS `pubDate`; Dublin Core `date` | 8,192 |
| RSS `description` when not selected as the article body | 65,536 |

Dublin Core means exactly `http://purl.org/dc/elements/1.1/`. Channel fields use the
same generic extraction rules and remain separate from item fields. No configured
publisher or inherited byline is fabricated. Attributes are preserved as sorted
expanded-name/value pairs; attribute values cap at 8,192, or 4,096 for `url`.
Element/attribute names cap at 8,192. GUID `isPermaLink`, when present, must be
`true` or `false`; its absence is not written back as invented source metadata.
References are inert supplied strings; their semantic validation and provenance
mapping remain the adapter's responsibility. HTTP(S)-prefix size classification
is not URL validity, permission or transport approval.

Exactly one required body is selected by the caller's **namespace URI and local
name**, never a guessed prefix or a default publisher mapping. `description` can
be selected; other named metadata fields cannot be used to bypass their caps.
Its complete XML-decoded string must be nonblank and at most **1 MiB in UTF-8**;
the batch aggregate is at most **6 MiB**. Preserve whitespace and original HTML
as inert text. Nested XML elements inside selected text fields reject rather than
being flattened or reconstructed. HTML must arrive as escaped text or CDATA.
Duplicate selected fields reject, even if values agree. Unknown extension
subtrees are not mapped or returned, but still face input/depth limits and take
part in native-ID conflict detection; their bytes remain in the caller's response.

A repeated GUID with identical parsed item content is preserved in input order;
a conflicting GUID rejects the whole batch. An internal SHA-256 fingerprint of
expanded element names, sorted attributes and character data includes unknown
item extensions. Character callback chunking and CDATA/entity spelling do not
change it; element order and whitespace do. Comments and prefix spelling do not.
This is only an intra-batch conflict check, **not** a new evidence identity or
public digest domain. Later adapters handle repeated identical observations and
explicit URL fallback identities. Each item carries its zero-based input index.

XML normalizes line endings and decodes XML entities, so the extracted HTML is
not a literal response-byte substring. There is no HTML unescape, sanitizer,
text extractor, link following or inferred article completeness here. Missing,
blank, structurally cut-off or over-limit content fails without fallback. A
well-formed summary/truncated article cannot be distinguished from a full article
by generic syntax alone: B1 and later source adapters must establish the field's
meaning/completeness. No suffix heuristic or invented completeness assertion.

## JSON catalog profile

Strict UTF-8, optional BOM, standard-library `json` with duplicate-key detection
at every object level. A string-aware preflight bounds container nesting before
decoding. Require a top-level object, a nonempty entry list at the caller's exact
key, and nonempty entry objects with nonblank string native IDs at the caller's
exact key. There are no CISA-specific field mappings or inferred catalog counts.
Preserve the complete document, envelope extensions, every entry field, nested
extension value, array order and supplied date strings. Source-schema validation,
declared count agreement and typed provenance belong to the later adapter.

All JSON keys/string values cap at 8,192 Unicode characters, with selected native
IDs capped at 256. These are the existing generic catalog metadata bounds;
RSS-specific title/byline caps are not silently imposed on arbitrary extension
keys. Escaped lone surrogates, duplicate keys (including equivalent escapes),
non-finite constants, invalid syntax and trailing data reject.

Integer tokens become exact Python integers with a deterministic **4,300-digit
safety ceiling** (excluding sign), independent of the interpreter's configurable
conversion threshold. Fraction/exponent tokens become exact finite `Decimal`
values: no binary-float rounding, underflow to zero or overflow to infinity.
Negative decimal zero is preserved. This is a parsing choice for review, not a
change to the existing `cti-json-v1` canonical profile: that profile still rejects
decimals and integers outside its approved safe range. A future adapter must
fail that incompatible source batch or seek a separately reviewed profile; never
coerce/drop unsupported values to make evidence hashable. Source numeric spelling
and whitespace remain available only in the original response bytes.

Repeated identical native-ID entries remain in order; differences anywhere in
an entry reject. Object key order is ignored, array order preserved, and comparison
is type-sensitive (booleans never equal integers; integers and decimals are
separate). Equal finite decimals compare by exact numeric value. No cross-source
identity, deduplication, revision generation or association is performed.

## Limits, validation and remaining gates

RSS input is at most **6 MiB**, catalog input **8 MiB**, including BOM/whitespace.
At most **500 RSS items** / **10,000 catalog entries**, including repeated IDs.
Maximum XML element depth and JSON object/array depth is **64**, root counted as
one. Bytes and characters are distinct; a multibyte article can hit its byte cap
before a same-length ASCII field. No cap changes, truncation or partial fallback.
The transport independently owns compressed/wire limits; these parsers cannot
infer transferred size from decoded bytes. Canonical-entry aggregate bytes remain
subject to existing digest/store/manifest validation after source mapping.

[Synthetic builders](../tests/parsing_cases.py) and
[focused tests](../tests/test_safe_parsing.py) cover exact/one-over input, body,
metadata, depth and item limits, namespace/encoding/entity behavior, incomplete
batches, duplicates, exact JSON decimals, existing integer-profile compatibility
and side-effect traps. Static import tests prohibit transport, storage, clock and
randomness dependencies. Full existing suites remain compatibility checks.

No dependencies added; no HTML parsing/sanitization/text extraction (M1-06b),
source adapters/mappings (M1-07–09), storage integration, live requests, article
fetches, real feed fixtures, scheduling, deployment, publication or paid services.
The 2 GiB storage and $0 paid-service limits remain. Issue #10 stays open for
separately approved B1 measurements. B1/B2/C remain unapproved. Stop at independent
review. M1-06a is delivered by PR #20; the separately approved
[M1-06b increment](M1_TRANSFORMS.md) now implements offline HTML/text helpers
without changing this parser profile or authorizing later gates.
