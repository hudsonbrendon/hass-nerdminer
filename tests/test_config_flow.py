"""Tests for NerdMiner config flow."""
from types import MappingProxyType
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.nerdminer.api import NerdMinerApiError, NerdMinerData
from custom_components.nerdminer.const import (
    CONF_BTC_ADDRESS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


async def test_user_flow_success(hass: HomeAssistant):
    with patch(
        "custom_components.nerdminer.config_flow.NerdMinerApiClient.fetch",
        AsyncMock(return_value=NerdMinerData(best_difficulty=0, workers_count=0, workers=[])),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_BTC_ADDRESS: "bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "NerdMiner (bc1qddjxw3…)"
        assert result["data"] == {CONF_BTC_ADDRESS: "bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02"}


async def test_user_flow_api_error(hass: HomeAssistant):
    with patch(
        "custom_components.nerdminer.config_flow.NerdMinerApiClient.fetch",
        AsyncMock(side_effect=NerdMinerApiError("nope")),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_BTC_ADDRESS: "bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_invalid_address(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BTC_ADDRESS: "not-a-real-address"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_address"}


async def test_options_flow(hass: HomeAssistant):
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="test",
        data={CONF_BTC_ADDRESS: "bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02"},
        source=config_entries.SOURCE_USER,
        options={},
        unique_id="bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02",
        discovery_keys=MappingProxyType({}),
    )
    hass.config_entries._entries[entry.entry_id] = entry

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_SCAN_INTERVAL: 60}
