# M1-05 offline hardened HTTPS transport

D030 implementation binding for independent review, 2026-11-24, M1 v1.3.
[Owner approval on PR #18](https://github.com/Ih4c/ghana-cti-pipeline/pull/18#issuecomment-7119629449)
authorizes D008/D014/D015 transport mechanisms using the standard library and
injected fakes only. Base: merged PR #18 (`e4d6a0a`). No live DNS/HTTP, endpoint
registry, robots/policy fetching, adapter, source parsing or storage integration.

## Inputs and boundaries

The caller supplies exact approved URLs, source ID, RSS/KEV limit class, project
contact URL/version, remaining attempt/time/byte budgets, optional conditional
context, resolver, socket factory, TLS context, clock, jitter and retrieval IDs.
Bounds are 16 approved URLs, 64 returned DNS addresses and a 64-character version
label. There are no default source endpoints, production resolver/socket factory or
implicit environment configuration. Explicit proxies are rejected; environment
proxy variables are never consulted. Direct egress still needs separate approval.

Endpoint profile: canonical ASCII DNS authorities, HTTPS, omitted port or 443,
no credentials, IP/legacy numeric literals, fragments, trailing host dot, dot path
segments, percent-encoded paths or ambiguous separators. Raw paths and queries
must exactly match an approved tuple; no prefix/fuzzy match or link discovery.
Unicode/encoded-path onboarding needs a separately reviewed profile, not guessing.
Malformed initial inputs raise a bounded input error rather than fabricate a URL
that the unchanged M1-01 failure schema could serialize. Unsafe redirect targets
produce a failure descriptor referring to the valid original request.

Resolve every hop/attempt anew with an explicit deadline. Validate every A/AAAA
answer before choosing one; reject mixed safe/unsafe answers, non-global/special
ranges, mapped IPv6 and metadata addresses. Explicit exclusions supplement
`ipaddress` across supported Python versions. Connect a numeric sockaddr directly;
never call a hostname connection helper or perform a second lookup. Verify the
connected peer; use the original approved hostname for Host, SNI and certificate
verification. Require CERT_REQUIRED, hostname checking and TLS 1.2 or newer.
Injected resolver/clock/socket implementations are trusted dependencies that must
honor deadlines; future real-host verification must prove that boundary.

## HTTP and content limits

A deliberately narrow HTTP/1.0–1.1 GET implementation handles bounded HTTP framing
only; no RSS/XML/JSON/HTML processing. No pooling, automatic redirects, cookies,
authentication, proxy tunnelling or resource requests. Fixed request headers use
`GhanaCTIPipeline/<version>` and a caller-supplied project contact URL.

Limit each response's status/header blocks, interim responses and trailers to
32 KiB aggregate;
reject malformed/duplicate headers, controls, obsolete folding and ambiguous
framing. At most four interim responses, no protocol upgrade. Support fixed
Content-Length, close-delimited bodies and simple chunked framing. Reject chunk
extensions and framing/representation/validator overrides in trailers. Preserve
only the descriptor's allowlisted validator/cache metadata; never expose raw
headers or error bodies. A 200 needs a bounded Content-Type declaration.

Independently bound HTTP wire-body octets (including chunk framing) and decoded
entity bytes to 6 MiB RSS / 8 MiB KEV. The descriptor's transferred_bytes counts
content-coded entity octets, excluding transfer framing, status and headers; the
wire cap is therefore at least as strict. Identity, one gzip member or zlib-wrapped
deflate are supported; reject other/stacked encodings, concatenation, trailing
compressed data and incomplete streams. Bounded decompression permits only one
excess output byte to detect overflow, never unbounded flush or silent truncation.
Only a complete 200 yields a decoded SHA-256 and separate transient body bytes.
No descriptor gains a storage/retention claim. A 304 yields no body or digest.

## Conditionals, retry and budgets

Conditional context includes a supplied original 200 descriptor and current ETag/
Last-Modified values. Only send validators at its exact final URL and redirect
chain; changed destinations receive none. An unsolicited or mismatched 304 fails.
New attempt IDs must be distinct within the call and from a supplied 200 anchor.
Transport verifies supplied context, not evidence backing, policy or retention;
checkpoint eligibility remains the caller's separately approved responsibility.

Maximum three redirects per attempt; each URL, DNS answer set and connection is
checked again. Maximum three caller-granted attempts, 5-second connect phase
(including resolver/TLS), 20-second read, 60-second attempt and 180-second source
budget, all reduced by caller grants. Redirects and backoff share those budgets.
Use an injected monotonic clock for deadlines; derive each attempt's end timestamp
from its aware UTC start plus elapsed monotonic time.

Retry only transient connection/timeout errors, 429 and 5xx. Backoff is 1, 2 …
seconds plus injected jitter in [0,1]; never retry before valid Retry-After.
Record a next-eligible timestamp and defer when that delay cannot fit. Invalid or
unrepresentable Retry-After stops safely. 403 pauses immediately. TLS, URL,
framing, decoding and size violations never retry. Attempt/byte/time grants are
consumed in-place, including failures, redirects and waits; no reset or persistence.

The byte grant is at most 512 MiB and covers reserved request bytes plus actually
read HTTP response octets, including headers/framing and failure traffic. It is
not a packet-level measure of DNS/TLS/IP overhead; the caller must reserve that
traffic before granting HTTP bytes. No global/day-reset accounting is implemented.
An exhausted grant returns no invented attempt. Separate call budgets isolate
sources. Safe M1-01 failure codes/statuses are preserved, including a received
200/304 followed by a transport error; raw exceptions never become descriptors.

## Review and stopping point

Tests use synthetic reserved-domain fixtures and injected resolver/socket/TLS/clock
objects, while blocking real DNS and socket connection calls. Test exact/over-limit
bytes/headers, deadlines, redirects, address families/rebinding, TLS/peer binding,
proxies, conditional context, compression bombs, retries and Retry-After deferral.
Existing contracts, protocols, dependencies and D027/article/storage/cost limits
stay unchanged. Issue #10 stays open for separately approved B1 measurements.

D030's narrow URL/HTTP/encoding profile and accounting semantics require review
and later source feasibility verification. No library deficiency requires a new
dependency. B1/B2/C, persisted operational budgets, source adapters and later
increments remain unapproved. Stop at the dedicated implementation PR.
