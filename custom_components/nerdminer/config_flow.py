"""Config flow for NerdMiner integration."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NerdMinerApiClient, NerdMinerApiError
from .const import CONF_BTC_ADDRESS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

# Bitcoin address regex (P2PKH/P2SH/Bech32). Permissive — relies on API for full validation.
BTC_ADDRESS_RE = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,89}$")


class NerdMinerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NerdMiner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_BTC_ADDRESS].strip()

            if not BTC_ADDRESS_RE.match(address):
                errors["base"] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                session = async_get_clientsession(self.hass)
                client = NerdMinerApiClient(session)
                try:
                    await client.fetch(address)
                except NerdMinerApiError:
                    errors["base"] = "cannot_connect"
                else:
                    truncated = address[:10] + "…"  # ellipsis
                    return self.async_create_entry(
                        title=f"NerdMiner ({truncated})",
                        data={CONF_BTC_ADDRESS: address},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_BTC_ADDRESS): str}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,  # noqa: ARG004
    ) -> OptionsFlow:
        return NerdMinerOptionsFlow()


class NerdMinerOptionsFlow(OptionsFlow):
    """Options flow for adjusting scan interval.

    HA assigns config_entry automatically; do not override __init__.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        int, vol.Range(min=10, max=3600)
                    ),
                }
            ),
        )
