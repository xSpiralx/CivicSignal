import pytest

from civicsignal_api.services.outbound import SafeOutboundClient, UnsafeOutboundRequest


async def test_outbound_requires_https_and_allowlisted_public_host(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    client = SafeOutboundClient({"data.example.gov"}, minimum_interval_seconds=0)

    async def public_resolution(host: str, port: int) -> frozenset[str]:
        return frozenset({"93.184.216.34"})

    monkeypatch.setattr(client, "_resolve", public_resolution)
    host, addresses = await client._validate_url("https://data.example.gov/resources.json")
    assert host == "data.example.gov"
    assert addresses == frozenset({"93.184.216.34"})
    with pytest.raises(UnsafeOutboundRequest, match="HTTPS"):
        await client._validate_url("http://data.example.gov/resources.json")
    with pytest.raises(UnsafeOutboundRequest, match="not approved"):
        await client._validate_url("https://other.example/resources.json")
    with pytest.raises(UnsafeOutboundRequest, match="credentials"):
        await client._validate_url("https://user:pass@data.example.gov/resources.json")


def test_outbound_rejects_every_non_public_address() -> None:
    for address in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "fe80::1", "fd00::1"):
        with pytest.raises(UnsafeOutboundRequest, match="non-public"):
            SafeOutboundClient._validate_ip(address)
