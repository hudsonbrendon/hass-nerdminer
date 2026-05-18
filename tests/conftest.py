"""Pytest fixtures shared across tests."""
import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ARG001
    """Enable loading of custom_components for all tests."""
    yield


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """HA test framework allows lingering tasks during teardown."""
    return True


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """HA test framework allows lingering timers during teardown."""
    return True
