"""Synthetic HTTP bytes and injected primitives; never resolves or connects a host."""

import socket
import ssl
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

from ghana_cti_pipeline.collectors.https_transport import HTTPSTransport
from ghana_cti_pipeline.collectors.transport_types import TransportBudget, TransportRequest

START = datetime(2026, 1, 15, 12, tzinfo=UTC)
URL = "https://example.org/feed"


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.waits = []

    def monotonic(self):
        return self.now

    def utcnow(self):
        return START + timedelta(seconds=self.now)

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds


class FakeSocket:
    def __init__(
        self,
        data=b"",
        *,
        clock=None,
        piece=16384,
        connect_error=None,
        receive_error=None,
        delay=0,
        peer=None,
        handshake_error=None,
    ):
        self.data = data
        self.offset = 0
        self.clock = clock
        self.piece = piece
        self.connect_error = connect_error
        self.receive_error = receive_error
        self.handshake_error = handshake_error
        self.delay = delay
        self.peer = peer
        self.connected = []
        self.sent = []
        self.timeouts = []
        self.closed = False

    def settimeout(self, timeout):
        self.timeouts.append(timeout)

    def connect(self, address):
        self.connected.append(address)
        if self.connect_error:
            raise self.connect_error

    def getpeername(self):
        return self.peer or self.connected[-1]

    def do_handshake(self):
        if self.handshake_error:
            raise self.handshake_error

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        if self.receive_error:
            raise self.receive_error
        if self.clock:
            self.clock.now += self.delay
        size = min(size, self.piece)
        data = self.data[self.offset : self.offset + size]
        self.offset += len(data)
        return data

    def close(self):
        self.closed = True


class FakeTLS:
    check_hostname = True
    verify_mode = ssl.CERT_REQUIRED
    minimum_version = ssl.TLSVersion.TLSv1_2

    def __init__(self):
        self.calls = []

    def wrap_socket(self, raw, **kwargs):
        self.calls.append(kwargs)
        return raw


class Harness:
    def __init__(self, sockets, *, answers=None, clock=None, id_start=1):
        self.clock = clock or FakeClock()
        self.sockets = sockets
        self.resolve_calls = []
        self.factory_calls = []
        self.answers = list(answers) if answers is not None else None
        self.tls = FakeTLS()
        self.identifiers = iter(UUID(int=i) for i in range(id_start, id_start + 100))
        self.transport = HTTPSTransport(
            resolver=self.resolve,
            socket_factory=self.socket,
            tls_context=self.tls,
            clock=self.clock,
            jitter=lambda: 0.25,
            id_factory=lambda: next(self.identifiers),
        )

    def resolve(self, host, port, timeout):
        self.resolve_calls.append((host, port, timeout))
        value = self.answers.pop(0) if self.answers is not None else ["1.1.1.1"]
        if isinstance(value, Exception):
            raise value
        return value

    def socket(self, family, kind, proto):
        index = len(self.factory_calls)
        self.factory_calls.append((family, kind, proto))
        assert kind == socket.SOCK_STREAM and proto == socket.IPPROTO_TCP
        return self.sockets[index]

    def fetch(self, request=None, budget=None):
        return self.transport.fetch(request or req(), budget or grant())


def req(**changes):
    return replace(
        TransportRequest(
            source_id="synthetic-feed",
            url=URL,
            approved_urls=(URL,),
            limit_class="rss",
            version="1.0.0",
            contact_url="https://example.org/project-contact",
        ),
        **changes,
    )


def grant(**changes):
    return replace(TransportBudget(3, 180, 512 * 1024**2), **changes)


def response(body=b"synthetic", *, status=200, headers=(), length=True):
    lines = [f"HTTP/1.1 {status} Synthetic"]
    names = {name.lower() for name, _ in headers}
    if status == 200 and "content-type" not in names:
        lines.append("Content-Type: application/octet-stream")
    if length and "content-length" not in names and "transfer-encoding" not in names:
        lines.append(f"Content-Length: {len(body)}")
    lines.extend(f"{name}: {value}" for name, value in headers)
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body
