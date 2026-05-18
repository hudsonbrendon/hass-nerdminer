from custom_components.nerdminer.const import (
    API_BASE_URL,
    CONF_BTC_ADDRESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def test_domain():
    assert DOMAIN == "nerdminer"


def test_defaults():
    assert DEFAULT_SCAN_INTERVAL == 30
    assert API_BASE_URL == "https://public-pool.io:40557/api/client"
    assert CONF_BTC_ADDRESS == "btc_address"
