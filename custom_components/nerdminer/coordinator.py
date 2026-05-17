"""DataUpdateCoordinator for NerdMiner integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NerdMinerApiClient, NerdMinerApiError, NerdMinerData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class NerdMinerCoordinator(DataUpdateCoordinator[NerdMinerData]):
    """Coordinator polling Public-Pool API for a single BTC address."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: NerdMinerApiClient,
        btc_address: str,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{btc_address[:10]}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._api = api
        self.btc_address = btc_address

    async def _async_update_data(self) -> NerdMinerData:
        """Fetch latest data; called by HA on update_interval."""
        try:
            return await self._api.fetch(self.btc_address)
        except NerdMinerApiError as err:
            raise UpdateFailed(str(err)) from err
