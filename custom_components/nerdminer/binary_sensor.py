"""Binary sensor platform for NerdMiner."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, BINARY_SENSOR_ONLINE, DOMAIN
from .coordinator import NerdMinerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NerdMiner binary sensors."""
    coordinator: NerdMinerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NerdMinerOnlineSensor(coordinator)])


class NerdMinerOnlineSensor(CoordinatorEntity[NerdMinerCoordinator], BinarySensorEntity):
    """True when at least one worker is reporting to the pool."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = BINARY_SENSOR_ONLINE
    _attr_name = "Online"

    def __init__(self, coordinator: NerdMinerCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.btc_address}_{BINARY_SENSOR_ONLINE}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.btc_address)},
            "name": f"NerdMiner {coordinator.btc_address[:10]}…",
            "manufacturer": "Public-Pool",
            "model": "Solo Bitcoin Miner",
        }

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.workers_count > 0
