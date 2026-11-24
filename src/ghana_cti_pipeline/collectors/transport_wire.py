"""Bounded HTTP framing and content decoding; no feed or source-document parsing."""

import re
import zlib

from ghana_cti_pipeline.collectors.transport_types import HEADER_LIMIT, TransportError, remaining

_TOKEN = re.compile(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+")
_STATUS = re.compile(rb"HTTP/1\.[01] ([1-5][0-9][0-9])(?: [\x20-\x7e]*)?\r\n")
_FORBIDDEN_TRAILERS = {
    "content-length",
    "transfer-encoding",
    "content-encoding",
    "content-type",
    "location",
    "etag",
    "last-modified",
    "cache-control",
    "vary",
    "retry-after",
}


class WireReader:
    def __init__(self, stream, budget, clock, deadline, body_limit):
        self.stream, self.budget, self.clock, self.deadline = stream, budget, clock, deadline
        self.body_limit = body_limit
        self.buffer = bytearray()
        self.header_bytes = 0
        self.body_bytes = 0
        self.body_mode = False
        self.status = None

    def _receive(self, size):
        remaining(self.clock, self.deadline, 20)
        if not self.budget.bytes_remaining:
            raise TransportError("body_limit")
        size = min(size, self.budget.bytes_remaining, 16384)
        read_deadline = min(self.deadline, self.clock.monotonic() + 20)
        self.stream.settimeout(remaining(self.clock, read_deadline, 20))
        data = self.stream.recv(size)
        if type(data) is not bytes or len(data) > size:
            raise TransportError("protocol_error")
        self.budget.charge(len(data))
        remaining(self.clock, read_deadline, 20)
        return data

    def _take(self, size):
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        if self.body_mode:
            self.body_bytes += len(data)
            if self.body_bytes > self.body_limit:
                raise TransportError("body_limit")
        return data

    def line(self, limit, *, header=False):
        while True:
            newline = self.buffer.find(b"\n")
            if newline >= 0:
                size = newline + 1
                if size > limit:
                    raise TransportError("header_limit" if header else "protocol_error")
                result = self._take(size)
                if not result.endswith(b"\r\n"):
                    raise TransportError("protocol_error")
                if header:
                    self.header_bytes += size
                    if self.header_bytes > HEADER_LIMIT:
                        raise TransportError("header_limit")
                return result
            if len(self.buffer) >= limit:
                raise TransportError("header_limit" if header else "protocol_error")
            data = self._receive(min(4096, limit - len(self.buffer)))
            if not data:
                raise TransportError("protocol_error")
            self.buffer.extend(data)

    def read(self, size):
        if not self.buffer:
            self.buffer.extend(self._receive(size))
        return self._take(min(size, len(self.buffer)))

    def exact(self, size):
        parts = bytearray()
        while len(parts) < size:
            data = self.read(size - len(parts))
            if not data:
                raise TransportError("protocol_error")
            parts.extend(data)
        return bytes(parts)

    def headers(self, *, trailers=False):
        result = {}
        while True:
            line = self.line(HEADER_LIMIT - self.header_bytes, header=True)
            if line == b"\r\n":
                return result
            name, separator, value = line[:-2].partition(b":")
            if not separator or not _TOKEN.fullmatch(name) or any(c < 32 or c > 126 for c in value):
                raise TransportError("protocol_error")
            name = name.decode("ascii").lower()
            if name in result or (trailers and name in _FORBIDDEN_TRAILERS):
                raise TransportError("protocol_error")
            result[name] = value.decode("ascii").strip()

    def head(self):
        for _ in range(5):
            line = self.line(HEADER_LIMIT - self.header_bytes, header=True)
            match = _STATUS.fullmatch(line)
            if not match:
                raise TransportError("protocol_error")
            self.status = int(match[1])
            headers = self.headers()
            if self.status == 101:
                raise TransportError("protocol_error")
            if self.status >= 200:
                self.framing(headers)
                return self.status, headers
            if "content-length" in headers or "transfer-encoding" in headers:
                raise TransportError("protocol_error")
        raise TransportError("header_limit")

    @staticmethod
    def framing(headers):
        transfer = headers.get("transfer-encoding")
        length = headers.get("content-length")
        if transfer is not None and (transfer.lower() != "chunked" or length is not None):
            raise TransportError("protocol_error")
        if length is not None and (not re.fullmatch(r"[0-9]{1,19}", length)):
            raise TransportError("protocol_error")
        return transfer is not None, int(length) if length is not None else None

    def chunks(self, headers):
        chunked, length = self.framing(headers)
        self.body_mode = True
        if length is not None and length > self.body_limit:
            raise TransportError("body_limit")
        if chunked:
            while True:
                line = self.line(128)
                if not re.fullmatch(rb"[0-9a-fA-F]{1,16}\r\n", line):
                    raise TransportError("protocol_error")
                size = int(line[:-2], 16)
                if size == 0:
                    self.headers(trailers=True)
                    return
                if size > self.body_limit - self.body_bytes:
                    raise TransportError("body_limit")
                while size:
                    part = self.exact(min(16384, size))
                    size -= len(part)
                    yield part
                if self.exact(2) != b"\r\n":
                    raise TransportError("protocol_error")
        elif length is not None:
            while length:
                part = self.exact(min(16384, length))
                length -= len(part)
                yield part
        else:
            while True:
                part = self.read(min(16384, self.body_limit - self.body_bytes + 1))
                if not part:
                    return
                yield part


def decode_body(reader, headers, clock, deadline):
    encoding = headers.get("content-encoding", "identity").lower()
    if encoding not in {"identity", "gzip", "deflate"}:
        raise TransportError("content_decoding_error")
    decoder = (
        None if encoding == "identity" else zlib.decompressobj(31 if encoding == "gzip" else 15)
    )
    body = bytearray()
    transferred = 0
    try:
        for chunk in reader.chunks(headers):
            remaining(clock, deadline, 20)
            transferred += len(chunk)
            output = (
                chunk
                if decoder is None
                else decoder.decompress(chunk, reader.body_limit - len(body) + 1)
            )
            if len(body) + len(output) > reader.body_limit:
                raise TransportError("body_limit")
            body.extend(output)
            if decoder is not None and decoder.unused_data:
                raise TransportError("content_decoding_error")
        if decoder is not None and (
            not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
        ):
            raise TransportError("content_decoding_error")
    except zlib.error:
        raise TransportError("content_decoding_error") from None
    remaining(clock, deadline, 20)
    return bytes(body), transferred, encoding
