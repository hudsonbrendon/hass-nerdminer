"""Tests for NerdMiner sensor platform."""
from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nerdminer.api import NerdMinerData, WorkerData
from custom_components.nerdminer.const import CONF_BTC_ADDRESS, DOMAIN


def _worker(**overrides) -> WorkerData:
    base = {
        "session_id": "s1",
        "name": "nerdminer1",
        "hash_rate": 78000,
        "start_time": "2026-05-17T10:00:00.000Z",
        "best_difficulty": 2.5,
        "last_seen": "2026-05-29T12:00:00.000Z",
    }
    base.update(overrides)
    return WorkerData(**base)


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
    data = NerdMinerData(best_difficulty=4.06, workers_count=1, workers=[_worker()])
    await _setup_with(hass, data)

    assert hass.states.get("sensor.nerdminer_bc1qtest_hashrate").state == "78.0"
    assert hass.states.get("sensor.nerdminer_bc1qtest_best_difficulty").state == "4.06"
    assert (
        hass.states.get("sensor.nerdminer_bc1qtest_worker_best_difficulty").state
        == "2.5"
    )
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "1"
    assert (
        hass.states.get("sensor.nerdminer_bc1qtest_start_time").state
        == "2026-05-17T10:00:00+00:00"
    )
    assert (
        hass.states.get("sensor.nerdminer_bc1qtest_last_seen").state
        == "2026-05-29T12:00:00+00:00"
    )
    assert hass.states.get("sensor.nerdminer_bc1qtest_session_accepted") is None
    assert hass.states.get("sensor.nerdminer_bc1qtest_session_difficulty") is None


async def test_aggregates_across_all_workers(hass: HomeAssistant):
    workers = [
        _worker(
            session_id="s1",
            hash_rate=78000,
            best_difficulty=2.5,
            last_seen="2026-05-29T12:00:00.000Z",
        ),
        _worker(
            session_id="s2",
            hash_rate=22000,
            best_difficulty=9.9,
            last_seen="2026-05-29T12:00:05.000Z",
        ),
    ]
    data = NerdMinerData(best_difficulty=4.06, workers_count=2, workers=workers)
    await _setup_with(hass, data)

    # hashrate sums: (78000 + 22000) / 1000 = 100.0 kH/s
    assert hass.states.get("sensor.nerdminer_bc1qtest_hashrate").state == "100.0"
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "2"
    # worker best difficulty is the max across workers
    assert (
        hass.states.get("sensor.nerdminer_bc1qtest_worker_best_difficulty").state
        == "9.9"
    )
    # last seen is the most recent worker timestamp
    assert (
        hass.states.get("sensor.nerdminer_bc1qtest_last_seen").state
        == "2026-05-29T12:00:05+00:00"
    )


async def test_sensors_no_worker_returns_none(hass: HomeAssistant):
    data = NerdMinerData(best_difficulty=0, workers_count=0, workers=[])
    await _setup_with(hass, data)

    state = hass.states.get("sensor.nerdminer_bc1qtest_hashrate")
    assert state.state == "unknown"
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "0"
    assert hass.states.get("sensor.nerdminer_bc1qtest_last_seen").state == "unknown"
