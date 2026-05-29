"""Sensor platform for NerdMiner."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import NerdMinerData
from .const import (
    ATTRIBUTION,
    DOMAIN,
    SENSOR_BEST_DIFFICULTY,
    SENSOR_HASHRATE,
    SENSOR_LAST_SEEN,
    SENSOR_START_TIME,
    SENSOR_WORKER_BEST_DIFFICULTY,
    SENSOR_WORKERS_COUNT,
)
from .coordinator import NerdMinerCoordinator


@dataclass(frozen=True, kw_only=True)
class NerdMinerSensorDescription(SensorEntityDescription):
    """Describes a NerdMiner sensor."""

    value_fn: Callable[[NerdMinerData], StateType | datetime]


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    """Parse an ISO 8601 string (possibly with milliseconds) to a timezone-aware datetime."""
    if not value:
        return None
    try:
        # Replace trailing Z with +00:00 for fromisoformat compatibility
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, AttributeError):
        return None


def _total_hashrate(data: NerdMinerData) -> float | None:
    """Sum hashrate across all workers and convert H/s -> kH/s."""
    if not data.workers:
        return None
    return sum(w.hash_rate for w in data.workers) / 1000


def _latest_last_seen(data: NerdMinerData) -> datetime | None:
    """Most recent moment any worker reported to the pool."""
    stamps = [
        ts
        for w in data.workers
        if (ts := _parse_iso_timestamp(w.last_seen)) is not None
    ]
    return max(stamps) if stamps else None


def _best_worker_difficulty(data: NerdMinerData) -> float | None:
    """Highest current-session best difficulty among connected workers."""
    if not data.workers:
        return None
    return max(w.best_difficulty for w in data.workers)


SENSOR_DESCRIPTIONS: tuple[NerdMinerSensorDescription, ...] = (
    NerdMinerSensorDescription(
        key=SENSOR_HASHRATE,
        translation_key=SENSOR_HASHRATE,
        name="Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_total_hashrate,
    ),
    NerdMinerSensorDescription(
        key=SENSOR_BEST_DIFFICULTY,
        translation_key=SENSOR_BEST_DIFFICULTY,
        name="Best difficulty",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda d: d.best_difficulty,
    ),
    NerdMinerSensorDescription(
        key=SENSOR_WORKER_BEST_DIFFICULTY,
        translation_key=SENSOR_WORKER_BEST_DIFFICULTY,
        name="Worker best difficulty",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=_best_worker_difficulty,
    ),
    NerdMinerSensorDescription(
        key=SENSOR_WORKERS_COUNT,
        translation_key=SENSOR_WORKERS_COUNT,
        name="Workers count",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.workers_count,
    ),
    NerdMinerSensorDescription(
        key=SENSOR_START_TIME,
        translation_key=SENSOR_START_TIME,
        name="Start time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _parse_iso_timestamp(d.workers[0].start_time) if d.workers else None,
    ),
    NerdMinerSensorDescription(
        key=SENSOR_LAST_SEEN,
        translation_key=SENSOR_LAST_SEEN,
        name="Last seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_latest_last_seen,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NerdMiner sensors."""
    coordinator: NerdMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        NerdMinerSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class NerdMinerSensor(CoordinatorEntity[NerdMinerCoordinator], SensorEntity):
    """Sensor entity backed by the coordinator."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    entity_description: NerdMinerSensorDescription

    def __init__(
        self,
        coordinator: NerdMinerCoordinator,
        description: NerdMinerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.btc_address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.btc_address)},
            "name": f"NerdMiner {coordinator.btc_address[:10]}…",
            "manufacturer": "Public-Pool",
            "model": "Solo Bitcoin Miner",
        }

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.coordinator.data)
