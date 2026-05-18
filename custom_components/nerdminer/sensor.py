"""Sensor platform for NerdMiner."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import NerdMinerData
from .const import (
    ATTRIBUTION,
    DOMAIN,
    SENSOR_BEST_DIFFICULTY,
    SENSOR_HASHRATE,
    SENSOR_SESSION_ACCEPTED,
    SENSOR_SESSION_DIFFICULTY,
    SENSOR_START_TIME,
    SENSOR_WORKERS_COUNT,
)
from .coordinator import NerdMinerCoordinator


@dataclass(frozen=True, kw_only=True)
class NerdMinerSensorDescription(SensorEntityDescription):
    """Describes a NerdMiner sensor."""

    value_fn: Callable[[NerdMinerData], float | int | str | None]


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


def _first_worker_attr(attr: str, *, scale: float = 1.0):
    def _get(data: NerdMinerData) -> float | int | str | None:
        if not data.workers:
            return None
        value = getattr(data.workers[0], attr)
        if scale != 1.0 and isinstance(value, (int, float)):
            return value * scale
        return value
    return _get


SENSOR_DESCRIPTIONS: tuple[NerdMinerSensorDescription, ...] = (
    NerdMinerSensorDescription(
        key=SENSOR_HASHRATE,
        translation_key=SENSOR_HASHRATE,
        name="Hashrate",
        native_unit_of_measurement="kH/s",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_first_worker_attr("hash_rate", scale=1 / 1000),
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
        key=SENSOR_SESSION_ACCEPTED,
        translation_key=SENSOR_SESSION_ACCEPTED,
        name="Session accepted",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_first_worker_attr("session_accepted"),
    ),
    NerdMinerSensorDescription(
        key=SENSOR_SESSION_DIFFICULTY,
        translation_key=SENSOR_SESSION_DIFFICULTY,
        name="Session difficulty",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=_first_worker_attr("session_difficulty"),
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
    def native_value(self) -> float | int | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
