"""Exact URL profiles and pure IP validation; no DNS or source registry."""

import ipaddress
import re
import socket
from urllib.parse import urlsplit

from ghana_cti_pipeline.collectors.transport_types import TransportInputError

_SPECIAL = tuple(
    ipaddress.ip_network(value)
    for value in (
        "192.0.0.0/24",
        "192.88.99.0/24",
        "192.31.196.0/24",
        "192.52.193.0/24",
        "192.175.48.0/24",
        "168.63.129.16/32",
        "64:ff9b::/96",
        "64:ff9b:1::/48",
        "2001::/23",
        "2002::/16",
        "3fff::/20",
        "2620:4f:8000::/48",
    )
)


def endpoint(url):
    if (
        type(url) is not str
        or not 1 <= len(url) <= 4096
        or any(not 33 <= ord(c) <= 126 for c in url)
        or "\\" in url
        or "#" in url
    ):
        raise TransportInputError("unsafe_url")
    try:
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 443}
            or parsed.netloc not in {host, host + ":443"}
            or len(host) > 253
            or "." not in host
            or any(
                not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                for label in host.split(".")
            )
            or not parsed.path.startswith("/")
            or "//" in parsed.path
            or "%" in parsed.path
            or any(part in {".", ".."} for part in parsed.path.split("/"))
            or re.search(r"%(?![0-9A-Fa-f]{2})", parsed.query)
        ):
            raise ValueError
        # inet_aton accepts legacy integer/octal/short IPv4 forms; never resolves DNS.
        try:
            socket.inet_aton(host)
        except OSError:
            pass
        else:
            raise ValueError
        return host, parsed.path, parsed.query
    except ValueError:
        raise TransportInputError("unsafe_url") from None


def validate_request(request):
    approved = {endpoint(url) for url in request.approved_urls}
    if endpoint(request.url) not in approved:
        raise TransportInputError("unsafe_url")
    endpoint(request.contact_url)
    if request.conditional:
        original = request.conditional.representation
        if original.source_id != request.source_id or original.requested_url != request.url:
            raise TransportInputError("protocol_error")
        if any(
            endpoint(url) not in approved for url in (*original.redirect_urls, original.final_url)
        ):
            raise TransportInputError("unsafe_url")
    return approved


def addresses(values):
    if type(values) not in {tuple, list} or not 1 <= len(values) <= 64:
        raise TransportInputError("unsafe_url")
    result = []
    for value in values:
        try:
            if type(value) is not str or "%" in value:
                raise ValueError
            ip = ipaddress.ip_address(value)
            if (
                not ip.is_global
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_unspecified
                or (
                    ip.version == 6
                    and (
                        ip.ipv4_mapped is not None
                        or ip.is_site_local
                        or ip not in ipaddress.ip_network("2000::/3")
                    )
                )
                or any(ip in network for network in _SPECIAL if network.version == ip.version)
            ):
                raise ValueError
        except ValueError:
            raise TransportInputError("unsafe_url") from None
        if ip not in result:
            result.append(ip)
    return tuple(result)
