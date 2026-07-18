import pytest

from civicsignal_api.pilot_seed import PILOT_SERVICES, seed_pilot


def test_pilot_manifest_is_small_authoritative_and_geographically_limited() -> None:
    assert 1 <= len(PILOT_SERVICES) <= 10
    assert len({item["key"] for item in PILOT_SERVICES}) == len(PILOT_SERVICES)
    for item in PILOT_SERVICES:
        assert item["sources"]
        assert all(url.startswith("https://") and ".dc.gov/" in url for _, url in item["sources"])
        assert item["locations"]
        assert item["eligibility"]


@pytest.mark.asyncio
async def test_pilot_seed_requires_a_named_human_reviewer() -> None:
    with pytest.raises(ValueError, match="human reviewer"):
        await seed_pilot(reviewer_name="AI")
