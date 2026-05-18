"""Tests for NerdMiner sensor platform."""
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.nerdminer.const import DOMAIN, CONF_BTC_ADDRESS
from custom_components.nerdminer.api import NerdMinerData, WorkerData


async def _setup_with(hass: HomeAssistant, data: NerdMinerData):
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
    return entry


async def test_sensors_with_active_worker(hass: HomeAssistant):
    worker = WorkerData(
        session_id="s1",
        name="nerdminer1",
        hash_rate=78000,
        start_time="2026-05-17T10:00:00.000Z",
        best_difficulty=2.5,
        session_difficulty=0.0016,
        session_accepted=42,
    )
    data = NerdMinerData(best_difficulty=4.06, workers_count=1, workers=[worker])
    await _setup_with(hass, data)

    assert hass.states.get("sensor.nerdminer_bc1qtest_hashrate").state == "78.0"
    assert hass.states.get("sensor.nerdminer_bc1qtest_best_difficulty").state == "4.06"
    assert hass.states.get("sensor.nerdminer_bc1qtest_session_accepted").state == "42"
    assert hass.states.get("sensor.nerdminer_bc1qtest_session_difficulty").state == "0.0016"
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "1"


async def test_sensors_no_worker_returns_none(hass: HomeAssistant):
    data = NerdMinerData(best_difficulty=0, workers_count=0, workers=[])
    await _setup_with(hass, data)

    state = hass.states.get("sensor.nerdminer_bc1qtest_hashrate")
    assert state.state in ("unknown", "0", "0.0")
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "0"
