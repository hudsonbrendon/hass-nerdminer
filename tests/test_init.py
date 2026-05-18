"""Tests for NerdMiner integration setup and unload."""
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nerdminer.const import (
    DOMAIN,
    CONF_BTC_ADDRESS,
    CONF_SCAN_INTERVAL,
)
from custom_components.nerdminer.api import NerdMinerData


async def test_setup_and_unload(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_BTC_ADDRESS: "bc1qtest"},
        options={CONF_SCAN_INTERVAL: 30},
        unique_id="bc1qtest",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.nerdminer.coordinator.NerdMinerApiClient.fetch",
        AsyncMock(return_value=NerdMinerData(best_difficulty=0, workers_count=0, workers=[])),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]

        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.entry_id not in hass.data.get(DOMAIN, {})
