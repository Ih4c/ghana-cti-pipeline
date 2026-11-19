# M1-01 retrieval and observation contracts

Implemented in [core/retrieval.py](../src/ghana_cti_pipeline/core/retrieval.py),
pending PR review; see [STATUS.md](STATUS.md). The
[owner approval](https://github.com/Ih4c/ghana-cti-pipeline/pull/7#issuecomment-6996754396)
covers only M1-01 under M1 v1.3, D011 and the descriptor portion of D019.
The [readiness specification](milestones/M1_READINESS.md) remains authoritative.

## Wire shape and validation

All five contracts have `schema_version: "1.0"` (defaulted on input, emitted on
serialization), required literal `kind`, frozen fields and forbidden extras.
This schema version is independent of the milestone version. Use `model_validate`
or `model_validate_json` at ingestion boundaries. `model_copy(update=..., deep=...)`
revalidates shallow and deep updates; nested descriptors are also revalidated.
Unchecked `model_construct` is not an ingestion API.

| Contract / kind | Fields and rules |
| --- | --- |
| `ResponseBodyMetadata` / `response_body_metadata` | `decoded_bytes`, `transferred_bytes`: strict integers, 0–8,388,608 inclusive; `media_type`, `content_encoding`: nonblank strict strings, 1–128 characters; `digest`: tagged value described below. No response bytes, paths, artifact IDs or retention flags. |
| `ReceivedResponse` / `received_response` | Attempt and response fields below; strict integer `status: 200`; required `body_metadata`. Describes a complete receipt, not parsing, retention or checkpoint success. |
| `NotModifiedResponse` / `not_modified_response` | Attempt and response fields; strict integer `status: 304`; `sent_etag` and/or `sent_last_modified` required non-null; required UUID `representation_retrieval_id`. No body descriptor, fresh body digest, snapshot or artifact. |
| `RetrievalFailure` / `retrieval_failure` | Attempt fields; nullable strict integer `status` in 100–599, finite `code`, strict boolean `retryable`. A received 200/304 can precede a transport validation failure; this is not a receipt-success record. No arbitrary exception text or partial body digest. |
| `EvidenceObservation` / `evidence_observation` | Required UUIDs `observation_id`, `retrieval_id`, `evidence_id`; `evidence_kind` and `evidence_schema_version` must be `v1`/`1.0` or `hybrid`/`2.0`; nonblank strict strings `locator` (1–4,096), `adapter_version` (1–128), `source_policy_id` (1–256), `source_policy_version` (1–128). Declared evidence linkage only; no EvidenceRevisionV2 implementation. |

Attempt fields: required `retrieval_id` UUID, nonblank strict `source_id` (1–256),
`requested_url`, `started_at` and `ended_at`. IDs/times are caller-supplied.
Times accept aware datetime objects or ISO datetime strings with explicit offsets;
numeric epochs, numeric strings, naive values and end-before-start reject.

Response fields: required `final_url`; `redirect_urls` is an immutable tuple of
up to three followed destinations (JSON array, default empty). Final URL equals
the last redirect, or the requested URL without redirects. Every URL is a strict
string of at most 4,096 characters, HTTPS, credential/fragment/control-free and
preserved verbatim. Malformed URLs/percent escapes, whitespace and backslashes
reject. This is syntactic validation, without DNS or SSRF protection.

Only these optional HTTP strings are accepted: `returned_etag`,
`returned_last_modified`, `cache_control`, `vary`, and the two sent validators on
304. They default to null; present values are nonblank strict strings of 1–1,024
characters without Unicode control/format characters. No arbitrary header map,
auth/cookie fields or raw header dump. Header grammar and the runtime aggregate
32 KiB limit belong to future transport; these are bounded metadata values.

`RetrievalOutcome` is a Pydantic discriminated union on `kind` for the 200, 304
and failure records. Failure codes are `timeout`, `connection_error`, `tls_error`,
`unsafe_url`, `redirect_limit`, `proxy_disallowed`, `header_limit`, `body_limit`,
`content_decoding_error`, `http_error`, `protocol_error`. Retryability is declared
metadata, not retry execution or permission.

The serialization choice for the specification's digest state is a nested
`digest` tagged value (`ResponseDigest`, discriminator `digest_state`):

- `ComputedDigest`: `digest_state: "computed"`, exactly 64 lowercase hex `sha256`
  characters, and required `domain: "decoded-http-entity-v1"`.
- `NotComputedDigest`: `digest_state: "not_computed"`, `sha256: null`, `domain: null`
  (both null fields may be omitted on input).

These frozen, extra-forbid value types also emit `schema_version: "1.0"`.
No hash is calculated or verified. The nested tag prevents contradictory states
and appears in the generated JSON schema. See the
[synthetic fixture](../tests/fixtures/retrieval.json) for complete wire examples;
its hashes and IDs are declared test values, not actual retrieval claims.

## Compatibility and remaining boundaries

Existing V1 models, serialized shapes, excerpt validation and
Collector/FetchedDocument/EvidenceRepository interfaces are unchanged. New models
import only the existing core contract and current Pydantic/standard library;
no dependencies, networking, storage, parser or source behavior is added.

These descriptors cannot resolve evidence IDs, establish that a referenced 200
was processed, reject a cross-source 304 link, or prove actual bytes, digest,
rights, retention, backing integrity or network safety. Later approved components
must enforce those rules, including no observations for 304s. No source is active.
The full-text strategic direction is unchanged.

No diagnostics/logging are implemented. Validation errors can include rejected
input; future diagnostics must use bounded safe codes rather than log raw input
or ValidationError representations.

[Acceptance tests](../tests/test_retrieval.py) cover exact/over-limit values,
discriminators, digest states, header allowlisting, UUID/time/URL rules, immutable
copies and V1 compatibility. Existing blocked-network and dependency tests remain
mandatory. The TLP inheritance xfail remains an unresolved later exporter gate.
