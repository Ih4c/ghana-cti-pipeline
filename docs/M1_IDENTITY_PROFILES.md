# M1-02b identity and digest profiles

Profile specification frozen before identity implementation, 2026-11-19.
[Owner approval](https://github.com/Ih4c/ghana-cti-pipeline/pull/9#issuecomment-6997682376)
covers M1 v1.3, D012/D025/D026 resolution, deterministic identities, SHA-256 helpers,
synthetic golden vectors and documentation. No persistence or source processing.

## D026 resolution and association keys

Existing V1, M1-01 and M1-02a serialized models remain unchanged. Their caller-supplied
IDs become verifiable through additive pure helpers, not new model defaults or
implicit migrations. New acquisitions must explicitly select `cti-identity-v1`.
Earlier synthetic profile labels remain valid descriptors but are not executable
identity profiles. Unknown helper profiles fail; never silently reinterpret history.

| Identity / future key | Exact identity projection |
| --- | --- |
| Logical item (`logical_item_id`) | Source ID plus typed source key (`native_id` or `original_url`, exact value). Same value with a different type/source is different. GUIDs are opaque native IDs; no trimming, URL normalization, title similarity or cross-source merging. |
| Source revision (`evidence_id`) | Computed logical item UUID, mode, original artifact domain/SHA-256, original article URL, publication descriptor, supplied publisher/byline only, and mode-specific source fields: feed title or complete typed catalog fields. Excludes configured publisher/byline, retrieval, response, locator/order, catalog release/context, policy, adapter/parser, transformations, derived output, supplied IDs and metadata_digest. |
| Derived representation | Computed source revision UUID, derived kind/domain/output SHA-256, complete transformation descriptor and parent identity/domain/SHA-256. Sanitized HTML names the source revision/original digest; plain text names the computed sanitized representation. Artifact association UUIDs are excluded. |
| Artifact association (`artifact_id`) | Complete validated artifact descriptor excluding only its own artifact_id. Includes policy, retrieval or parent association, locator, digest and transformation metadata. Build response then original then derivatives, updating parent IDs explicitly. Same bytes do not imply shared acquisition or rights. |
| Evidence association (new computed key, no wire field) | Domain-tagged canonical evidence metadata digest. That digest covers the full validated V2 bundle except its own metadata_digest, including computed source IDs, retrieval/policy, artifact associations, derived versions, catalog context and markings. Future storage key is association UUID; evidence_id is a nonunique grouping foreign key for bundles. |
| Processing manifest (`manifest_id`) | Domain-tagged manifest digest. Digest covers full validated manifest except root manifest_id and root digest, preserving item/artifact array order and nested evidence digests. No self-reference. |
| Retrieval observation (`observation_id`) | Full validated M1-01 observation excluding only observation_id. Includes retrieval ID, evidence kind/version/ID, locator, adapter and policy versions. Retries of the same observation are idempotent; distinct retrieval UUIDs give distinct observations. Chronology comes from retrieval timestamps, never UUID ordering. |

UUID names are canonical UTF-8 JSON envelopes `{"profile":"cti-identity-v1","projection":...}`.
UUIDv5 uses the namespace below and this exact JSON string (RFC UUIDv5 SHA-1,
not SHA-256 substituted into the UUID algorithm). No random UUIDs, current times,
checkout paths, hostnames or process-global state participate.

A → B → A returns the first A source revision UUID again; observations/associations
preserve each acquisition. A changed sanitizer/extractor creates new derived IDs,
not a source revision. Even identical output bytes get distinct derived IDs when
the original source revision or parent derivation differs. Storage must reject
same association ID with different canonical content and must never overwrite a
bundle keyed only by evidence_id. Helpers do not resurrect deleted content or
authorize re-acquisition; policy/lifecycle enforcement belongs to later storage.

## Fixed namespaces

These constants are UUIDv5(NAMESPACE_URL,
`https://github.com/Ih4c/ghana-cti-pipeline/identity/v1/` + the role).
Their values are frozen even if the repository is renamed or transferred.

| Role | UUID namespace |
| --- | --- |
| logical-item | `c9dd1d2a-e8b2-5fba-b58b-100562599777` |
| source-revision | `f4798c76-659b-5f49-81a8-fb47a85ca766` |
| derived-representation | `5b9b8f86-4d66-55f2-8845-124e0ee93ff2` |
| artifact-association | `c4be50e4-6b83-54d9-bda5-9c36c8ef5536` |
| evidence-association | `fa9ff4b2-257d-5d99-b309-e202770d59b0` |
| processing-manifest | `b69acd17-2d88-5151-9f49-09eb68cbb0f4` |
| retrieval-observation | `a4ab0ac4-f3a5-5177-a262-2bb9df3ff261` |

## Canonical JSON: cti-json-v1

Accept only exact Python dict/list/str/int/bool/None JSON values. Dict keys must
be exact strings; object keys sort by Unicode code point, arrays preserve order.
No coercion, tuple/set/custom objects, duplicate-key parsing or automatic date/UUID
conversion. This helper serializes an existing tree; it does not parse JSON text.
Integers are limited to ±(2^53−1). All floats (including finite values, negative
zero, NaN and infinities) reject; a future numeric profile requires explicit review.

Output: UTF-8 without BOM, ensure_ascii=False, compact separators `,` and `:`,
standard JSON escaping for quotes/backslashes/control characters, no trailing
newline. Preserve Unicode scalars exactly: no NFC/NFKC, trimming, newline, entity,
HTML or URL normalization. Lone surrogates reject. Missing keys and explicit null
remain distinct. This is this project's versioned profile, not RFC 8785/JCS.

Maximum encoded JSON is 8 MiB, maximum container nesting is 64 (root container
counts as one). Cycles and unsupported values reject. Input objects are not mutated.
Model projections use validated model_dump(mode="json", exclude_none=False), with
all defaults materialized. UUIDs use lowercase hyphenated strings and dates use
ISO strings from the existing models. Parsed timestamps retain their offset;
supplied publication text remains exact. Equivalent instants written with different
offsets may have different metadata digests; no silent time normalization occurs.

## Digest domains and bytes

The seven supported domains are closed; unknown domains/profiles reject before
processing. `compute_digest` returns an immutable domain/SHA-256 pair. SHA-256
always hashes the exact bytes specified below, without a prefix/suffix. This keeps
M1-01's decoded-entity hash and existing artifact semantics intact. Domain separation
is the mandatory `(domain, sha256)` pair; equal bytes in different domains have equal
hex but distinct typed digests. Identity projections carry domains and role-specific
UUID namespaces. Never use bare hex as a cross-domain identity or rights key.

| Domain | Input and byte encoding | Helper limit |
| --- | --- | --- |
| decoded-http-entity-v1 | Exact bytes after content decoding, before character decoding | 0–8 MiB |
| feed-field-html-utf8-v1 | Exact str encoded strict UTF-8, no HTML/XML parsing | 0–1 MiB |
| sanitized-html-utf8-v1 | Caller-supplied str encoded strict UTF-8, no sanitization | 0–1 MiB |
| plain-text-utf8-v1 | Caller-supplied str encoded strict UTF-8, no extraction | 0–1 MiB |
| catalog-entry-json-v1 | Complete supplied entry JSON object, cti-json-v1 | 0–8 MiB encoded |
| evidence-metadata-json-v1 | Evidence projection above, cti-json-v1 | 0–8 MiB encoded |
| processing-manifest-json-v1 | Manifest projection above, cti-json-v1 | 0–8 MiB encoded |

Empty bytes/text can be hashed, but M1-02a still rejects empty item artifacts as
full-text completion. Lowercase 64-hex output and strict domain types integrate
with existing descriptors; no hash is proof of authenticity, rights or retention.
Identity helpers use declared original/output digests; future ingestion/storage
must compare them with actual bytes. They do not parse content to verify metadata.

## Integration order and limits

Compute content digests, fill artifact descriptors and assign artifact association
IDs from parents to children. Compute logical/source-revision IDs and copy them
into the V2 bundle. Compute metadata_digest, then evidence association UUID. Build
manifest item links/digests, compute manifest digest and UUID. Observations use
the independently supplied retrieval UUID and source revision UUID. Reprocessing
can create new associations/manifests without fabricating a retrieval observation.
Helpers return values; callers explicitly apply validated model_copy updates.

No automatic state lookup/mutation, content storage, networking, clock, filesystem
access, parsers, sanitizers, adapters or publication. Canonicalization/identity
profiles and namespaces are compatibility boundaries; future changes need new
profiles, vectors and migration decisions. M1-03 needs its own approval and must
enforce immutable associations, reference integrity and lifecycle rules.

## API and validation evidence

[digests.py](../src/ghana_cti_pipeline/core/digests.py) exposes `canonical_json`,
`compute_digest` and immutable `ContentDigest`. Structured digest domains require
an object root; raw strings containing JSON are not parsed. Identity APIs live in
[identities.py](../src/ghana_cti_pipeline/core/identities.py): `logical_item_id`,
`source_revision_projection`, `source_revision_id`, `derived_representation_id`,
`artifact_association_id`, `evidence_metadata_digest`, `evidence_association_id`,
`processing_manifest_digest`, `processing_manifest_id`, `retrieval_observation_id`.

Evidence metadata hashing checks that the bundle carries computed logical/revision
IDs; evidence/manifest association helpers check their stored metadata digest.
Artifact ID assignment is explicit. External artifact bytes, referenced evidence
bundles and lifecycle state are not resolved; M1-03 must verify those relationships.

[Fixed vectors](../tests/fixtures/identity_vectors.json) contain 11 identity scenarios,
five canonical JSON vectors and seven domain digest vectors. Expected values were
calculated independently with stdlib json/hashlib/uuid, without application helpers;
tests compare literal expected values, not outputs regenerated from the implementation.
Coverage includes all seven namespaces, A→B→A, Unicode normalization distinctions,
source and typed-key separation, transform changes and metadata/manifest associations.
[Identity tests](../tests/test_identity_helpers.py) also block filesystem/network/
clock/randomness during helper calls; digest tests exercise limits and process seeds.
