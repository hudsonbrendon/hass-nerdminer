"""Tests for the NerdMiner binary sensor platform."""
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nerdminer.api import NerdMinerData, WorkerData
from custom_components.nerdminer.const import CONF_BTC_ADDRESS, DOMAIN


async def _setup(hass, data):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_BTC_ADDRESS: "bc1qtest"},
        unique_id="bc1qtest",
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.nerdminer.coordinator.NerdMinerApiClient.fetch",
        AsyncMock(return_value=data),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


async def test_online_when_worker_active(hass: HomeAssistant):
    worker = WorkerData(
        session_id="s", name="w", hash_rate=1, start_time="",
        best_difficulty=0, last_seen="",
    )
    await _setup(hass, NerdMinerData(best_difficulty=0, workers_count=1, workers=[worker]))
    state = hass.states.get("binary_sensor.nerdminer_bc1qtest_online")
    assert state.state == "on"


async def test_offline_when_no_workers(hass: HomeAssistant):
    await _setup(hass, NerdMinerData(best_difficulty=0, workers_count=0, workers=[]))
    state = hass.states.get("binary_sensor.nerdminer_bc1qtest_online")
    assert state.state == "off"
