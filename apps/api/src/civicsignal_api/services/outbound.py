import asyncio
import ipaddress
import logging
import socket
import time
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

MAX_RESPONSE_BYTES = 2_097_152
MAX_REDIRECTS = 3
ALLOWED_CONTENT_TYPES = {
    "application/json",
    "text/csv",
    "text/plain",
}
USER_AGENT = "CivicSignal/1.0 (+https://github.com/xSpiralx/CivicSignal)"
logger = logging.getLogger(__name__)


class UnsafeOutboundRequest(ValueError):
    pass


@dataclass(frozen=True)
class SafeResponse:
    url: str
    content: bytes
    content_type: str
    etag: str | None


class SafeOutboundClient:
    def __init__(
        self,
        allowed_hosts: set[str],
        *,
        minimum_interval_seconds: float = 1.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not allowed_hosts:
            raise ValueError("An explicit source hostname allowlist is required")
        self.allowed_hosts = {host.casefold().rstrip(".") for host in allowed_hosts}
        self.minimum_interval_seconds = minimum_interval_seconds
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._transport = transport

    @staticmethod
    def _validate_ip(value: str) -> None:
        address = ipaddress.ip_address(value.split("%", 1)[0])
        if not address.is_global:
            raise UnsafeOutboundRequest("Outbound destination resolved to a non-public address")

    async def _resolve(self, host: str, port: int) -> frozenset[str]:
        try:
            answers = await asyncio.get_running_loop().getaddrinfo(
                host, port, type=socket.SOCK_STREAM
            )
        except socket.gaierror as exc:
            raise UnsafeOutboundRequest("Outbound hostname could not be resolved") from exc
        addresses = frozenset(answer[4][0] for answer in answers)
        if not addresses:
            raise UnsafeOutboundRequest("Outbound hostname returned no addresses")
        for address in addresses:
            self._validate_ip(address)
        return addresses

    async def _validate_url(self, url: str) -> tuple[str, frozenset[str]]:
        parsed = urlsplit(url)
        if parsed.scheme != "https":
            raise UnsafeOutboundRequest("Only HTTPS source URLs are allowed")
        if parsed.username or parsed.password:
            raise UnsafeOutboundRequest("Embedded URL credentials are not allowed")
        host = (parsed.hostname or "").casefold().rstrip(".")
        if not host or host not in self.allowed_hosts:
            raise UnsafeOutboundRequest("Outbound hostname is not approved for this source")
        if parsed.port not in (None, 443):
            raise UnsafeOutboundRequest("Non-standard outbound ports are not allowed")
        return host, await self._resolve(host, 443)

    async def _rate_limit(self, host: str) -> None:
        async with self._locks[host]:
            delay = self.minimum_interval_seconds - (time.monotonic() - self._last_request[host])
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_request[host] = time.monotonic()

    async def get(self, url: str) -> SafeResponse:
        current = url
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(connect=5, read=15, write=5, pool=5),
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
            transport=self._transport,
        ) as client:
            for redirect_count in range(MAX_REDIRECTS + 1):
                host, initial_addresses = await self._validate_url(current)
                await self._rate_limit(host)
                logger.info("source_fetch_start", extra={"source_host": host})
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        if redirect_count == MAX_REDIRECTS:
                            raise UnsafeOutboundRequest("Source redirect limit exceeded")
                        location = response.headers.get("location")
                        if not location:
                            raise UnsafeOutboundRequest("Source redirect omitted a location")
                        current = urljoin(current, location)
                        continue
                    response.raise_for_status()
                    network_stream = response.extensions.get("network_stream")
                    if network_stream is not None and hasattr(network_stream, "get_extra_info"):
                        peer = network_stream.get_extra_info("server_addr")
                        if peer:
                            peer_address = str(peer[0])
                            self._validate_ip(peer_address)
                            if peer_address not in initial_addresses:
                                raise UnsafeOutboundRequest(
                                    "Connected source address was not in the validated DNS answer"
                                )
                    content_type = (
                        response.headers.get("content-type", "").split(";", 1)[0].casefold()
                    )
                    if content_type not in ALLOWED_CONTENT_TYPES:
                        raise UnsafeOutboundRequest("Source response content type is not allowed")
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                        raise UnsafeOutboundRequest("Source response is too large")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise UnsafeOutboundRequest("Source response is too large")
                final_addresses = await self._resolve(host, 443)
                if initial_addresses != final_addresses:
                    raise UnsafeOutboundRequest("Source DNS answers changed during the request")
                logger.info(
                    "source_fetch_complete",
                    extra={"source_host": host, "response_bytes": len(body)},
                )
                return SafeResponse(
                    current, bytes(body), content_type, response.headers.get("etag")
                )
        raise UnsafeOutboundRequest("Source request failed")
