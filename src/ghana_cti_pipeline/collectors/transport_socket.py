"""Pinned numeric sockets with original-host TLS; all I/O dependencies injected."""

import ipaddress
import socket
import ssl

from ghana_cti_pipeline.collectors.transport_policy import addresses
from ghana_cti_pipeline.collectors.transport_types import TransportError, remaining


def close_socket(stream):
    if stream is not None:
        try:
            stream.close()
        except OSError:
            pass


def connect_pinned(host, *, resolver, socket_factory, tls_context, clock, deadline, attempt):
    if (
        not tls_context.check_hostname
        or tls_context.verify_mode != ssl.CERT_REQUIRED
        or tls_context.minimum_version < ssl.TLSVersion.TLSv1_2
    ):
        raise TransportError("tls_error")
    deadline = min(deadline, clock.monotonic() + 5)
    resolved = addresses(resolver(host, 443, remaining(clock, deadline, 5)))
    remaining(clock, deadline, 5)
    ip = resolved[attempt % len(resolved)]
    family = socket.AF_INET if ip.version == 4 else socket.AF_INET6
    raw = socket_factory(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    secured = None
    try:
        raw.settimeout(remaining(clock, deadline, 5))
        address = (str(ip), 443) if ip.version == 4 else (str(ip), 443, 0, 0)
        raw.connect(address)
        peer = raw.getpeername()
        if ipaddress.ip_address(peer[0]) != ip or peer[1] != 443:
            raise TransportError("unsafe_url")
        raw.settimeout(remaining(clock, deadline, 5))
        secured = tls_context.wrap_socket(raw, server_hostname=host, do_handshake_on_connect=False)
        secured.settimeout(remaining(clock, deadline, 5))
        secured.do_handshake()
        remaining(clock, deadline, 5)
        peer = secured.getpeername()
        if ipaddress.ip_address(peer[0]) != ip or peer[1] != 443:
            raise TransportError("unsafe_url")
        return secured
    except BaseException:
        close_socket(secured)
        close_socket(raw)
        raise
