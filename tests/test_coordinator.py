"""Tests for DataUpdateCoordinator."""
from unittest.mock import AsyncMock
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.nerdminer.api import NerdMinerApiError, NerdMinerData
from custom_components.nerdminer.coordinator import NerdMinerCoordinator


async def test_coordinator_success(hass):
    api = AsyncMock()
    api.fetch.return_value = NerdMinerData(
        best_difficulty=1.5, workers_count=1, workers=[]
    )
    coord = NerdMinerCoordinator(hass, api, "bc1qtest", scan_interval=30)

    data = await coord._async_update_data()

    assert data.best_difficulty == 1.5
    api.fetch.assert_awaited_once_with("bc1qtest")


async def test_coordinator_api_failure_raises_update_failed(hass):
    api = AsyncMock()
    api.fetch.side_effect = NerdMinerApiError("boom")
    coord = NerdMinerCoordinator(hass, api, "bc1qtest", scan_interval=30)

    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_coordinator_interval_configurable(hass):
    api = AsyncMock()
    coord = NerdMinerCoordinator(hass, api, "bc1qtest", scan_interval=120)
    assert coord.update_interval.total_seconds() == 120
