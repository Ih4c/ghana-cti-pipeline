"""Offline-testable HTTPS orchestration; no default endpoints or real-I/O dependencies."""

import errno
import hashlib
import math
import socket
import ssl
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

from ghana_cti_pipeline.collectors.transport_policy import endpoint, validate_request
from ghana_cti_pipeline.collectors.transport_socket import close_socket, connect_pinned
from ghana_cti_pipeline.collectors.transport_types import (
    HEADER_LIMIT,
    TransportError,
    TransportInputError,
    TransportResult,
    header_value,
    remaining,
    retrieval_id,
)
from ghana_cti_pipeline.collectors.transport_wire import WireReader, decode_body
from ghana_cti_pipeline.core.retrieval import (
    NotModifiedResponse,
    ReceivedResponse,
    ResponseBodyMetadata,
    RetrievalFailure,
)

_REDIRECTS = {301, 302, 303, 307, 308}
_TRANSIENT = {
    errno.ECONNRESET,
    errno.ECONNREFUSED,
    errno.ECONNABORTED,
    errno.ENETUNREACH,
    errno.EHOSTUNREACH,
    errno.ENETDOWN,
    errno.EPIPE,
    errno.ETIMEDOUT,
}


class _Clock:
    def __init__(self, clock):
        self.clock = clock
        self.last = -math.inf

    def monotonic(self):
        value = self.clock.monotonic()
        if type(value) not in {int, float} or not math.isfinite(value) or value < self.last:
            raise TransportInputError("protocol_error")
        self.last = value
        return value

    def utcnow(self):
        value = self.clock.utcnow()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise TransportInputError("protocol_error")
        return value

    def sleep(self, seconds):
        self.clock.sleep(seconds)


def _error(error):
    if isinstance(error, TransportError):
        return TransportError(error.code, retryable=error.retryable)
    if isinstance(error, TransportInputError):
        return TransportError(str(error))
    if isinstance(error, ssl.SSLError):
        return TransportError("tls_error")
    if isinstance(error, TimeoutError):
        return TransportError("timeout", retryable=True)
    if isinstance(error, socket.gaierror):
        return TransportError("connection_error", retryable=error.errno == socket.EAI_AGAIN)
    if isinstance(error, OSError):
        return TransportError(
            "connection_error",
            retryable=isinstance(error, ConnectionError) or error.errno in _TRANSIENT,
        )
    return TransportError("protocol_error")


def _response_metadata(headers):
    return {
        field: header_value(headers.get(name))
        for field, name in (
            ("returned_etag", "etag"),
            ("returned_last_modified", "last-modified"),
            ("cache_control", "cache-control"),
            ("vary", "vary"),
        )
    }


def _retry_after(value, now):
    if value is None:
        return None
    header_value(value)
    try:
        if value.isascii() and value.isdecimal():
            if len(value) > 10 or int(value) > 2**31 - 1:
                raise ValueError
            delay = int(value)
        else:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                raise ValueError
            delay = max(0, (date - now).total_seconds())
        return now + timedelta(seconds=delay)
    except (ValueError, TypeError, OverflowError):
        raise TransportError("protocol_error") from None


def _validators(request, url, redirects):
    conditional = request.conditional
    if conditional and (
        url == conditional.representation.final_url
        and tuple(redirects) == conditional.representation.redirect_urls
    ):
        return conditional.etag, conditional.last_modified
    return None, None


def _request_bytes(request, url, validators):
    host, path, query = endpoint(url)
    target = path + ("?" + query if query else "")
    headers = [
        f"GET {target} HTTP/1.1",
        f"Host: {host}",
        f"User-Agent: GhanaCTIPipeline/{request.version} (+{request.contact_url})",
        "Accept-Encoding: gzip, deflate, identity",
        "Connection: close",
    ]
    for name, value in zip(("If-None-Match", "If-Modified-Since"), validators, strict=True):
        if value is not None:
            headers.append(f"{name}: {value}")
    data = ("\r\n".join(headers) + "\r\n\r\n").encode("ascii")
    if len(data) > HEADER_LIMIT:
        raise TransportError("header_limit")
    return data


class HTTPSTransport:
    def __init__(
        self, *, resolver, socket_factory, tls_context, clock, jitter, id_factory, proxy=None
    ):
        if proxy is not None:
            raise TransportInputError("proxy_disallowed")
        self.resolver = resolver
        self.socket_factory = socket_factory
        self.tls_context = tls_context
        self.clock = clock
        self.jitter = jitter
        self.id_factory = id_factory

    def fetch(self, request, budget):
        approved = validate_request(request)
        budget.__post_init__()
        clock = _Clock(self.clock)
        start = clock.monotonic()
        source_deadline = start + budget.seconds_remaining
        outcomes = []
        used = {request.conditional.representation.retrieval_id} if request.conditional else set()
        try:
            while (
                budget.attempts_remaining
                and budget.bytes_remaining
                and clock.monotonic() < source_deadline
            ):
                attempt_index = len(outcomes)
                identifier = retrieval_id(self.id_factory, used)
                budget.attempts_remaining -= 1
                started = clock.utcnow()
                tick = clock.monotonic()
                deadline = min(source_deadline, tick + 60)
                outcome, body, retry_at = self._attempt(
                    request,
                    approved,
                    budget,
                    clock,
                    deadline,
                    attempt_index,
                    identifier,
                    started,
                    tick,
                )
                outcomes.append(outcome)
                if not isinstance(outcome, RetrievalFailure):
                    return TransportResult(tuple(outcomes), "complete", body)
                if not outcome.retryable:
                    return TransportResult(tuple(outcomes), "paused")
                jitter = self.jitter()
                if (
                    type(jitter) not in {int, float}
                    or not math.isfinite(jitter)
                    or not 0 <= jitter <= 1
                ):
                    raise TransportInputError("protocol_error")
                delay = 2**attempt_index + jitter
                if retry_at is not None:
                    delay = max(delay, (retry_at - outcome.ended_at).total_seconds())
                eligible = outcome.ended_at + timedelta(seconds=delay)
                if delay >= source_deadline - clock.monotonic():
                    return TransportResult(tuple(outcomes), "deferred", next_eligible_at=eligible)
                if not budget.attempts_remaining or not budget.bytes_remaining:
                    return TransportResult(tuple(outcomes), "exhausted", next_eligible_at=eligible)
                clock.sleep(delay)
            return TransportResult(tuple(outcomes), "exhausted")
        finally:
            budget.seconds_remaining = max(
                0, budget.seconds_remaining - (clock.monotonic() - start)
            )

    def _attempt(
        self, request, approved, budget, clock, deadline, attempt_index, identifier, started, tick
    ):
        url, redirects, seen = request.url, [], {request.url}
        reader = None
        retry_at = None
        status = None
        base = {
            "retrieval_id": identifier,
            "source_id": request.source_id,
            "requested_url": request.url,
            "started_at": started,
        }
        try:
            while True:
                if endpoint(url) not in approved:
                    raise TransportError("unsafe_url")
                stream = None
                reader = None
                try:
                    validators = _validators(request, url, redirects)
                    data = _request_bytes(request, url, validators)
                    if len(data) > budget.bytes_remaining:
                        raise TransportError("body_limit")
                    stream = connect_pinned(
                        endpoint(url)[0],
                        resolver=self.resolver,
                        socket_factory=self.socket_factory,
                        tls_context=self.tls_context,
                        clock=clock,
                        deadline=deadline,
                        attempt=attempt_index,
                    )
                    remaining(clock, deadline, 20)
                    budget.charge(len(data))  # Reserve even if sendall fails after a partial send.
                    send_deadline = min(deadline, clock.monotonic() + 20)
                    stream.settimeout(remaining(clock, send_deadline, 20))
                    stream.sendall(data)
                    remaining(clock, send_deadline, 20)
                    reader = WireReader(stream, budget, clock, deadline, request.body_limit)
                    status, headers = reader.head()
                    remaining(clock, deadline, 20)
                    metadata = _response_metadata(headers)
                    if status in _REDIRECTS:
                        if len(redirects) == 3:
                            raise TransportError("redirect_limit")
                        location = headers.get("location")
                        if not location:
                            raise TransportError("protocol_error")
                        target = urljoin(url, location)
                        if endpoint(target) not in approved:
                            raise TransportError("unsafe_url")
                        if target in seen:
                            raise TransportError("protocol_error")
                        redirects.append(target)
                        seen.add(target)
                        url = target
                        continue
                    response = {"final_url": url, "redirect_urls": tuple(redirects), **metadata}
                    if status == 304:
                        if validators == (None, None):
                            raise TransportError("protocol_error")
                        return (
                            NotModifiedResponse(
                                kind="not_modified_response",
                                status=304,
                                **base,
                                **response,
                                ended_at=started + timedelta(seconds=clock.monotonic() - tick),
                                sent_etag=validators[0],
                                sent_last_modified=validators[1],
                                representation_retrieval_id=request.conditional.representation.retrieval_id,
                            ),
                            None,
                            None,
                        )
                    if status == 200:
                        media = headers.get("content-type", "")
                        if not 1 <= len(media) <= 128:
                            raise TransportError("protocol_error")
                        body, transferred, encoding = decode_body(reader, headers, clock, deadline)
                        descriptor = ResponseBodyMetadata(
                            kind="response_body_metadata",
                            decoded_bytes=len(body),
                            transferred_bytes=transferred,
                            media_type=media,
                            content_encoding=encoding,
                            digest={
                                "digest_state": "computed",
                                "sha256": hashlib.sha256(body).hexdigest(),
                                "domain": "decoded-http-entity-v1",
                            },
                        )
                        remaining(clock, deadline, 20)
                        return (
                            ReceivedResponse(
                                kind="received_response",
                                status=200,
                                **base,
                                **response,
                                ended_at=started + timedelta(seconds=clock.monotonic() - tick),
                                body_metadata=descriptor,
                            ),
                            body,
                            None,
                        )
                    transient = status == 429 or 500 <= status <= 599
                    if transient:
                        now = started + timedelta(seconds=clock.monotonic() - tick)
                        retry_at = _retry_after(headers.get("retry-after"), now)
                    raise TransportError("http_error", retryable=transient)
                finally:
                    close_socket(stream)
        except Exception as error:
            failure = _error(error)
            if reader is not None and reader.status is not None:
                status = reader.status
            return (
                RetrievalFailure(
                    kind="retrieval_failure",
                    **base,
                    ended_at=started + timedelta(seconds=clock.monotonic() - tick),
                    status=status,
                    code=failure.code,
                    retryable=failure.retryable,
                ),
                None,
                retry_at,
            )
