"""Hardened transport tests use only injected fakes and synthetic HTTP messages."""

import errno
import gzip
import hashlib
import socket
import ssl
import zlib
from datetime import timedelta

import pytest
from transport_fakes import START, URL, FakeClock, FakeSocket, Harness, grant, req, response

from ghana_cti_pipeline.collectors.transport_types import (
    DAILY_LIMIT,
    HEADER_LIMIT,
    KEV_LIMIT,
    RSS_LIMIT,
    Conditional,
    TransportInputError,
)
from ghana_cti_pipeline.core.retrieval import (
    NotModifiedResponse,
    ReceivedResponse,
    RetrievalFailure,
)


@pytest.fixture(autouse=True)
def no_real_network_or_dns(monkeypatch):
    attempted = []

    def denied(*args, **kwargs):
        attempted.append(True)
        raise AssertionError("Real network and DNS forbidden in offline transport tests")

    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "create_connection"):
        monkeypatch.setattr(socket, name, denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    yield
    assert not attempted


def assert_failure(result, code, status=None, retryable=False):
    failure = result.outcomes[-1]
    assert isinstance(failure, RetrievalFailure)
    assert (failure.code, failure.status, failure.retryable) == (code, status, retryable)
    assert result.body is None
    assert "SENSITIVE_SYNTHETIC" not in repr(result)
    return failure


def test_complete_200_pins_ip_host_tls_and_preserves_descriptor_shape(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://unapproved.example.org:8080")
    monkeypatch.setenv("ALL_PROXY", "http://unapproved.example.org:8080")
    stream = FakeSocket(
        response(
            b"synthetic complete body",
            headers=(("ETag", '"v1"'), ("Set-Cookie", "SENSITIVE_SYNTHETIC")),
        )
    )
    harness = Harness([stream])
    budget = grant()
    result = harness.fetch(budget=budget)
    receipt = result.outcomes[0]
    assert isinstance(receipt, ReceivedResponse)
    assert receipt.status == 200 and receipt.schema_version == "1.0"
    assert receipt.body_metadata.decoded_bytes == receipt.body_metadata.transferred_bytes == 23
    assert receipt.body_metadata.digest.sha256 == hashlib.sha256(result.body).hexdigest()
    assert receipt.body_metadata.digest.domain == "decoded-http-entity-v1"
    assert receipt.returned_etag == '"v1"'
    assert "SENSITIVE_SYNTHETIC" not in receipt.model_dump_json()
    assert "synthetic complete body" not in repr(result)
    assert stream.connected == [("1.1.1.1", 443)]
    assert harness.tls.calls == [
        {"server_hostname": "example.org", "do_handshake_on_connect": False}
    ]
    sent = stream.sent[0]
    assert b"Host: example.org\r\n" in sent
    assert b"GhanaCTIPipeline/1.0.0 (+https://example.org/project-contact)" in sent
    assert b"Proxy" not in sent and b"Cookie" not in sent
    assert budget.attempts_remaining == 2
    assert budget.bytes_remaining == DAILY_LIMIT - len(sent) - len(stream.data)
    assert max(stream.timeouts) <= 20 and stream.timeouts[0] <= 5
    assert stream.closed


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org/feed",
        "https://user:secret@example.org/feed",
        "https://example.org:444/feed",
        "https://127.0.0.1/feed",
        "https://127.1/feed",
        "https://2130706433/feed",
        "https://0177.0.0.1/feed",
        "https://0x7f000001/feed",
        "https://[::1]/feed",
        "https://example.org./feed",
        "https://EXAMPLE.org/feed",
        "https://example.org/feed#fragment",
        "https://example.org/a/../feed",
        "https://example.org/%2Ffeed",
        "https://example.org//feed",
        "https://example.org/feed\r\nX: bad",
        "https://example.org\\@other.org/feed",
        "https://éxample.org/feed",
    ],
)
def test_unsafe_initial_urls_are_bounded_input_errors_without_io(url):
    harness = Harness([])
    with pytest.raises(TransportInputError, match="^unsafe_url$"):
        harness.fetch(req(url=url, approved_urls=(url,)))
    assert not harness.resolve_calls and not harness.factory_calls


def test_approval_is_exact_path_and_query_not_prefix():
    harness = Harness([])
    for url in (URL + "/other", URL + "?other=1", "https://other.org/feed"):
        with pytest.raises(TransportInputError, match="unsafe_url"):
            harness.fetch(req(url=url))
    assert not harness.resolve_calls


@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",
        "10.0.0.1",
        "172.16.0.1",
        "192.168.1.1",
        "169.254.169.254",
        "100.100.100.200",
        "168.63.129.16",
        "192.0.0.9",
        "192.0.2.1",
        "192.88.99.1",
        "192.31.196.1",
        "192.52.193.1",
        "192.175.48.1",
        "198.18.0.1",
        "224.0.0.1",
        "240.0.0.1",
        "::1",
        "::",
        "fc00::1",
        "fe80::1",
        "fec0::1",
        "ff02::1",
        "::ffff:1.1.1.1",
        "64:ff9b::a9fe:a9fe",
        "2001:db8::1",
        "2002:7f00:1::1",
        "2001::1",
        "3fff::1",
        "2620:4f:8000::1",
        "2606:4700::1%eth0",
    ],
)
def test_every_dns_answer_must_be_global_and_nonspecial(ip):
    harness = Harness([], answers=[["1.1.1.1", ip]])
    result = harness.fetch()
    assert_failure(result, "unsafe_url")
    assert len(harness.resolve_calls) == 1 and not harness.factory_calls


def test_ipv6_numeric_connection_and_no_second_lookup():
    stream = FakeSocket(response())
    harness = Harness([stream], answers=[["2606:4700:4700::1111"]])
    assert harness.fetch().disposition == "complete"
    assert stream.connected == [("2606:4700:4700::1111", 443, 0, 0)]
    assert harness.factory_calls[0][0] == socket.AF_INET6
    assert len(harness.resolve_calls) == 1


def test_rebinding_is_rechecked_on_retry_and_redirect():
    first = FakeSocket(connect_error=ConnectionResetError(errno.ECONNRESET, "SENSITIVE_SYNTHETIC"))
    harness = Harness([first], answers=[["1.1.1.1"], ["127.0.0.1"]])
    result = harness.fetch()
    assert_failure(result, "unsafe_url")
    assert len(result.outcomes) == 2 and len(harness.factory_calls) == 1
    redirect = "https://example.org/new"
    first = FakeSocket(response(b"", status=302, headers=(("Location", redirect),)))
    harness = Harness([first], answers=[["1.1.1.1"], ["169.254.169.254"]])
    result = harness.fetch(req(approved_urls=(URL, redirect)))
    assert_failure(result, "unsafe_url", 302)
    assert len(harness.resolve_calls) == 2 and len(harness.factory_calls) == 1


@pytest.mark.parametrize("fault", ["hostname", "certificate", "version", "peer", "handshake"])
def test_tls_and_peer_failures_do_not_retry(fault):
    stream = FakeSocket(response())
    harness = Harness([stream])
    if fault == "hostname":
        harness.tls.check_hostname = False
    elif fault == "certificate":
        harness.tls.verify_mode = ssl.CERT_NONE
    elif fault == "version":
        harness.tls.minimum_version = ssl.TLSVersion.TLSv1
    elif fault == "peer":
        stream.peer = ("8.8.8.8", 443)
    else:
        stream.handshake_error = ssl.SSLCertVerificationError("SENSITIVE_SYNTHETIC")
    result = harness.fetch()
    assert_failure(result, "unsafe_url" if fault == "peer" else "tls_error")
    assert len(result.outcomes) == 1
    assert not stream.sent


def test_explicit_proxy_is_rejected():
    from ghana_cti_pipeline.collectors.https_transport import HTTPSTransport

    with pytest.raises(TransportInputError, match="proxy_disallowed"):
        HTTPSTransport(
            resolver=None,
            socket_factory=None,
            tls_context=None,
            clock=None,
            jitter=None,
            id_factory=None,
            proxy="http://example.org/proxy",
        )


@pytest.mark.parametrize("encoding", ["identity", "gzip", "deflate"])
@pytest.mark.parametrize("size", [0, 1, RSS_LIMIT, RSS_LIMIT + 1])
def test_rss_exact_decoded_and_wire_bounds(encoding, size):
    body = b"x" * size
    encoded = (
        body
        if encoding == "identity"
        else (gzip.compress(body) if encoding == "gzip" else zlib.compress(body))
    )
    stream = FakeSocket(response(encoded, headers=(("Content-Encoding", encoding),)))
    result = Harness([stream]).fetch()
    if size > RSS_LIMIT:
        assert_failure(result, "body_limit", 200)
    else:
        assert result.body == body
        metadata = result.outcomes[0].body_metadata
        assert metadata.decoded_bytes == size and metadata.transferred_bytes == len(encoded)


def test_kev_exact_wire_limit_is_independent_of_rss():
    for size in (KEV_LIMIT, KEV_LIMIT + 1):
        stream = FakeSocket(response(b"k" * size))
        result = Harness([stream]).fetch(req(limit_class="kev"))
        if size == KEV_LIMIT:
            assert len(result.body) == KEV_LIMIT
        else:
            assert_failure(result, "body_limit", 200)


@pytest.mark.parametrize(
    "body,encoding",
    [
        (b"not gzip", "gzip"),
        (gzip.compress(b"synthetic")[:-1], "gzip"),
        (gzip.compress(b"a") + gzip.compress(b"b"), "gzip"),
        (gzip.compress(b"a") + b"tail", "gzip"),
        (b"", "gzip"),
        (b"synthetic", "br"),
        (gzip.compress(b"a"), "gzip, gzip"),
        (zlib.compress(b"a")[2:-4], "deflate"),
    ],
)
def test_unsupported_incomplete_and_concatenated_encodings_fail(body, encoding):
    result = Harness(
        [FakeSocket(response(body, headers=(("Content-Encoding", encoding),)))]
    ).fetch()
    assert_failure(result, "content_decoding_error", 200)
    assert len(result.outcomes) == 1


def test_header_exact_limit_and_one_over_preserve_received_status():
    base = response(b"", headers=(("X-Padding", ""),))
    for extra in (0, 1):
        message = response(b"", headers=(("X-Padding", "x" * (HEADER_LIMIT - len(base) + extra)),))
        assert len(message) == HEADER_LIMIT + extra
        result = Harness([FakeSocket(message)]).fetch()
        if extra:
            assert_failure(result, "header_limit", 200)
        else:
            assert isinstance(result.outcomes[0], ReceivedResponse)


@pytest.mark.parametrize(
    "headers",
    [
        (("Content-Length", "1"), ("Content-Length", "1")),
        (("Content-Length", "1"), ("Transfer-Encoding", "chunked")),
        (("Transfer-Encoding", "gzip"),),
        (("Content-Length", "-1"),),
        (("Content-Length", "+1"),),
        (("ETag", "x" * 1025),),
        (("Content-Type", "x" * 129),),
        (("X-Header", "a\tb"),),
    ],
)
def test_ambiguous_or_invalid_headers_fail_without_partial_body(headers):
    result = Harness([FakeSocket(response(b"x", headers=headers))]).fetch()
    assert_failure(result, "protocol_error", 200)


def test_chunked_and_close_delimited_messages():
    for data, headers in (
        (
            b"3\r\nabc\r\n2\r\nde\r\n0\r\nX-Trailer: safe\r\n\r\n",
            (("Transfer-Encoding", "chunked"),),
        ),
        (b"abcde", ()),
    ):
        result = Harness(
            [FakeSocket(response(data, headers=headers, length=False), piece=1)]
        ).fetch()
        assert result.body == b"abcde"
        assert result.outcomes[0].body_metadata.transferred_bytes == 5


@pytest.mark.parametrize(
    "body",
    [
        b"1\r\na!\r\n0\r\n\r\n",
        b"1;ext=1\r\na\r\n0\r\n\r\n",
        b"0\r\nETag: override\r\n\r\n",
        b"invalid\r\n",
        b"1\r\n",
    ],
)
def test_malformed_chunks_or_unsafe_trailers_fail(body):
    result = Harness(
        [FakeSocket(response(body, headers=(("Transfer-Encoding", "chunked"),), length=False))]
    ).fetch()
    assert_failure(result, "protocol_error", 200)


def test_conditional_304_has_no_body_digest_and_matches_original_representation():
    first = Harness([FakeSocket(response(headers=(("ETag", '"v1"'),)))]).fetch().outcomes[0]
    stream = FakeSocket(
        response(b"", status=304, headers=(("ETag", '"v2"'), ("Content-Length", "999999999")))
    )
    result = Harness([stream], id_start=100).fetch(req(conditional=Conditional(first, etag='"v1"')))
    receipt = result.outcomes[0]
    assert isinstance(receipt, NotModifiedResponse)
    assert receipt.representation_retrieval_id == first.retrieval_id
    assert b'If-None-Match: "v1"\r\n' in stream.sent[0]
    assert result.body is None and "body_metadata" not in receipt.model_dump()
    assert_failure(Harness([FakeSocket(response(b"", status=304))]).fetch(), "protocol_error", 304)


def test_changed_redirect_does_not_forward_old_validators():
    original = Harness([FakeSocket(response())]).fetch().outcomes[0]
    target = "https://example.org/changed"
    redirect = FakeSocket(response(b"", status=302, headers=(("Location", target),)))
    unsolicited = FakeSocket(response(b"", status=304))
    harness = Harness([redirect, unsolicited], id_start=100)
    result = harness.fetch(
        req(approved_urls=(URL, target), conditional=Conditional(original, etag='"v1"'))
    )
    assert b"If-None-Match" in redirect.sent[0]
    assert b"If-None-Match" not in unsolicited.sent[0]
    assert_failure(result, "protocol_error", 304)


def test_redirect_chain_three_passes_and_four_fails():
    urls = (URL, *(f"https://example.org/hop{i}" for i in range(1, 5)))
    for hops in (3, 4):
        sockets = [
            FakeSocket(response(b"", status=302, headers=(("Location", urls[i + 1]),)))
            for i in range(hops)
        ]
        sockets.append(FakeSocket(response()))
        harness = Harness(sockets)
        result = harness.fetch(req(approved_urls=urls))
        if hops == 3:
            assert result.outcomes[0].redirect_urls == urls[1:4]
            assert len(harness.resolve_calls) == 4
        else:
            assert_failure(result, "redirect_limit", 302)
            assert len(harness.resolve_calls) == 4 and not sockets[-1].connected
        assert all(stream.closed for stream in sockets[: len(harness.factory_calls)])


@pytest.mark.parametrize(
    "status,retryable", [(403, False), (401, False), (404, False), (429, True), (503, True)]
)
def test_http_retry_rules_and_403_pause(status, retryable):
    streams = [FakeSocket(response(b"SENSITIVE_SYNTHETIC", status=status)), FakeSocket(response())]
    harness = Harness(streams)
    result = harness.fetch()
    assert isinstance(result.outcomes[0], RetrievalFailure)
    assert result.outcomes[0].retryable is retryable
    assert len(result.outcomes) == (2 if retryable else 1)
    assert harness.clock.waits == ([1.25] if retryable else [])
    assert result.disposition == ("complete" if retryable else "paused")


def test_retry_after_fitting_and_deferral():
    for value in ("120", "Thu, 15 Jan 2026 12:02:00 GMT"):
        stream = FakeSocket(response(b"", status=429, headers=(("Retry-After", value),)))
        harness = Harness([stream])
        budget = grant(seconds_remaining=30)
        result = harness.fetch(budget=budget)
        assert_failure(result, "http_error", 429, True)
        assert result.disposition == "deferred" and result.next_eligible_at == START + timedelta(
            seconds=120
        )
        assert not harness.clock.waits and budget.attempts_remaining == 2
    streams = [
        FakeSocket(response(b"", status=503, headers=(("Retry-After", "10"),))),
        FakeSocket(response()),
    ]
    harness = Harness(streams)
    assert harness.fetch().disposition == "complete"
    assert harness.clock.waits == [10]


def test_invalid_retry_after_never_causes_immediate_retry():
    for value in ("invalid", "-1", "9" * 100):
        harness = Harness(
            [FakeSocket(response(b"", status=429, headers=(("Retry-After", value),)))]
        )
        assert_failure(harness.fetch(), "protocol_error", 429)
        assert not harness.clock.waits


def test_attempt_and_byte_grants_are_consumed_without_reset():
    streams = [FakeSocket(connect_error=TimeoutError("SENSITIVE_SYNTHETIC")) for _ in range(3)]
    harness = Harness(streams)
    budget = grant()
    result = harness.fetch(budget=budget)
    assert len(result.outcomes) == 3 and result.disposition == "exhausted"
    assert len({record.retrieval_id for record in result.outcomes}) == 3
    assert harness.clock.waits == [1.25, 2.25]
    assert budget.attempts_remaining == 0 and budget.seconds_remaining == 176.5
    assert not harness.fetch(budget=budget).outcomes
    harness = Harness([])
    assert_failure(harness.fetch(budget=grant(bytes_remaining=1)), "body_limit")
    assert not harness.resolve_calls


def test_connect_and_read_deadlines_and_source_time_bound():
    harness = Harness([])

    def slow_dns(host, port, timeout):
        assert timeout == 5
        harness.clock.now += 5
        return ["1.1.1.1"]

    harness.transport.resolver = slow_dns
    result = harness.fetch(budget=grant(attempts_remaining=1))
    assert_failure(result, "timeout", retryable=True)
    assert not harness.factory_calls
    clock = FakeClock()
    stream = FakeSocket(response(b"x" * 100), clock=clock, piece=1, delay=1)
    harness = Harness([stream], clock=clock)
    result = harness.fetch(budget=grant(attempts_remaining=1, seconds_remaining=7))
    assert_failure(result, "timeout", retryable=True)
    assert clock.now == 7 and max(stream.timeouts) <= 7


def test_safe_failure_and_source_isolation():
    bad = Harness([FakeSocket(receive_error=ValueError("SENSITIVE_SYNTHETIC"))])
    assert_failure(bad.fetch(), "protocol_error")
    good = Harness([FakeSocket(response())])
    assert good.fetch().disposition == "complete"


def test_read_timeout_and_attempt_timeout_are_separate():
    clock = FakeClock()
    stream = FakeSocket(response(), clock=clock, delay=21)
    result = Harness([stream], clock=clock).fetch(budget=grant(attempts_remaining=1))
    assert_failure(result, "timeout", retryable=True)
    assert stream.timeouts[-1] == 20
    clock = FakeClock()
    stream = FakeSocket(response(), clock=clock, piece=1, delay=15)
    result = Harness([stream], clock=clock).fetch(budget=grant(attempts_remaining=1))
    assert_failure(result, "timeout", retryable=True)
    assert clock.now == 60


def test_source_budget_includes_all_attempts_and_waits():
    clock = FakeClock()

    class TimedSocket(FakeSocket):
        def recv(self, size):
            clock.now += min(15, self.timeouts[-1])
            if self.timeouts[-1] <= 15:
                raise TimeoutError("synthetic bounded timeout")
            return super().recv(size)

    streams = [TimedSocket(response(), piece=1) for _ in range(3)]
    harness = Harness(streams, clock=clock)
    budget = grant()
    result = harness.fetch(budget=budget)
    assert len(result.outcomes) == 3
    assert clock.now == 180 and budget.seconds_remaining == 0
    assert all(record.code == "timeout" for record in result.outcomes)


def test_send_timeout_discards_response_before_reading():
    clock = FakeClock()
    stream = FakeSocket(response())
    harness = Harness([stream], clock=clock)

    def late_send(data):
        clock.now += 21

    stream.sendall = late_send
    assert_failure(harness.fetch(budget=grant(attempts_remaining=1)), "timeout", retryable=True)
    assert stream.offset == 0 and stream.closed


@pytest.mark.parametrize("temporary", [False, True])
def test_only_temporary_dns_failures_retry(temporary):
    code = socket.EAI_AGAIN if temporary else socket.EAI_NONAME
    harness = Harness(
        [FakeSocket(response())],
        answers=[socket.gaierror(code, "SENSITIVE_SYNTHETIC"), ["1.1.1.1"]],
    )
    result = harness.fetch()
    assert result.outcomes[0].code == "connection_error"
    assert result.outcomes[0].retryable is temporary
    assert len(result.outcomes) == (2 if temporary else 1)
    assert len(harness.resolve_calls) == (2 if temporary else 1)


def test_compressed_transfer_limit_is_independent_of_decoded_limit():
    import random

    body = random.Random(17).randbytes(RSS_LIMIT)
    encoded = gzip.compress(body)
    assert len(encoded) > RSS_LIMIT
    result = Harness(
        [FakeSocket(response(encoded, headers=(("Content-Encoding", "gzip"),)))]
    ).fetch()
    assert_failure(result, "body_limit", 200)


def test_chunk_framing_counts_toward_wire_limit():
    for extra in (0, 1):
        size = RSS_LIMIT - 15 + extra
        data = f"{size:x}\r\n".encode() + b"x" * size + b"\r\n0\r\n\r\n"
        assert len(data) == RSS_LIMIT + extra
        result = Harness(
            [FakeSocket(response(data, headers=(("Transfer-Encoding", "chunked"),), length=False))]
        ).fetch()
        if extra:
            assert_failure(result, "body_limit", 200)
        else:
            assert len(result.body) == size
            assert result.outcomes[0].body_metadata.transferred_bytes == size


def test_header_limit_aggregates_interim_responses_and_trailers():
    prefix = b"HTTP/1.1 103 Early Hints\r\nX-Pad: "
    suffix = b"\r\n\r\n" + response(b"")
    for extra in (0, 1):
        data = prefix + b"x" * (HEADER_LIMIT - len(prefix) - len(suffix) + extra) + suffix
        result = Harness([FakeSocket(data)]).fetch()
        if extra:
            assert_failure(result, "header_limit", 200)
        else:
            assert result.body == b""
    message = response(
        b"0\r\nX-Pad: " + b"x" * HEADER_LIMIT + b"\r\n\r\n",
        headers=(("Transfer-Encoding", "chunked"),),
        length=False,
    )
    assert_failure(Harness([FakeSocket(message)]).fetch(), "header_limit", 200)


def test_interim_count_and_protocol_upgrade_fail_closed():
    hint = b"HTTP/1.1 103 Early Hints\r\n\r\n"
    assert Harness([FakeSocket(hint * 4 + response())]).fetch().disposition == "complete"
    assert_failure(Harness([FakeSocket(hint * 5 + response())]).fetch(), "header_limit", 103)
    assert_failure(Harness([FakeSocket(response(b"", status=101))]).fetch(), "protocol_error", 101)


def test_supplied_304_anchor_cannot_be_reused_as_new_retrieval_id():
    first = Harness([FakeSocket(response())]).fetch().outcomes[0]
    harness = Harness([])
    with pytest.raises(TransportInputError, match="protocol_error"):
        harness.fetch(req(conditional=Conditional(first, etag='"v1"')))
    assert not harness.resolve_calls


def test_matching_redirect_context_sends_validators_only_at_final_hop():
    target = "https://example.org/final"
    initial = FakeSocket(response(b"", status=302, headers=(("Location", "/final"),)))
    anchor = (
        Harness([initial, FakeSocket(response())])
        .fetch(req(approved_urls=(URL, target)))
        .outcomes[0]
    )
    initial = FakeSocket(response(b"", status=302, headers=(("Location", "/final"),)))
    final = FakeSocket(response(b"", status=304))
    harness = Harness([initial, final], id_start=100)
    result = harness.fetch(
        req(
            approved_urls=(URL, target),
            conditional=Conditional(anchor, last_modified="synthetic-validator"),
        )
    )
    assert isinstance(result.outcomes[0], NotModifiedResponse)
    assert result.outcomes[0].redirect_urls == (target,)
    assert b"If-Modified-Since" not in initial.sent[0]
    assert b"If-Modified-Since: synthetic-validator" in final.sent[0]


def test_unsafe_redirect_is_never_resolved_or_followed():
    for target in (
        "http://example.org/feed",
        "https://169.254.169.254/metadata",
        "https://example.org/unapproved",
    ):
        harness = Harness([FakeSocket(response(b"", status=302, headers=(("Location", target),)))])
        assert_failure(harness.fetch(), "unsafe_url", 302)
        assert len(harness.resolve_calls) == 1


def test_exact_descriptor_header_bounds_and_no_partial_hash_after_eof():
    result = Harness(
        [FakeSocket(response(headers=(("ETag", "x" * 1024), ("Content-Type", "x" * 128))))]
    ).fetch()
    assert len(result.outcomes[0].returned_etag) == 1024
    truncated = response(b"short", headers=(("Content-Length", "20"),))
    failure = assert_failure(Harness([FakeSocket(truncated)]).fetch(), "protocol_error", 200)
    assert "sha256" not in failure.model_dump_json()


@pytest.mark.parametrize(
    "changes",
    [
        {"attempts_remaining": 4},
        {"attempts_remaining": True},
        {"seconds_remaining": 181},
        {"seconds_remaining": float("nan")},
        {"bytes_remaining": DAILY_LIMIT + 1},
        {"bytes_remaining": -1},
        {"bytes_remaining": True},
    ],
)
def test_caller_cannot_expand_or_coerce_budget_caps(changes):
    with pytest.raises(TransportInputError):
        grant(**changes)


def test_exhausted_budgets_make_no_calls_and_byte_charge_is_shared_across_retries():
    for limits in ({"attempts_remaining": 0}, {"seconds_remaining": 0}, {"bytes_remaining": 0}):
        harness = Harness([])
        result = harness.fetch(budget=grant(**limits))
        assert result.outcomes == () and not harness.resolve_calls
    first = FakeSocket(response(b"", status=503))
    second = FakeSocket(response(b"synthetic final"))
    budget = grant()
    result = Harness([first, second]).fetch(budget=budget)
    assert result.disposition == "complete"
    expected = sum(len(stream.sent[0]) + stream.offset for stream in (first, second))
    assert DAILY_LIMIT - budget.bytes_remaining == expected


def test_single_response_byte_budget_exhaustion_has_no_success_or_overrun():
    stream = FakeSocket(response(b"x" * 4096))
    budget = grant(bytes_remaining=1024)
    result = Harness([stream]).fetch(budget=budget)
    assert_failure(result, "body_limit", 200)
    assert budget.bytes_remaining == 0
    assert stream.offset + len(stream.sent[0]) == 1024
