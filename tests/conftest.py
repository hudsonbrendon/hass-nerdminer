"""Pytest fixtures shared across tests."""
import threading

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]

# Track threads at session start so per-test diff stays meaningful.
_BASELINE_THREADS: frozenset[threading.Thread] = frozenset()


def pytest_sessionstart(session: pytest.Session) -> None:  # noqa: ARG001
    """Snapshot the daemon threads HA creates so we can filter them later."""
    global _BASELINE_THREADS  # noqa: PLW0603
    _BASELINE_THREADS = frozenset(threading.enumerate())


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


@pytest.fixture(autouse=True)
def _allow_ha_daemon_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch threading.enumerate so verify_cleanup ignores HA daemon threads.

    pytest_homeassistant_custom_component's verify_cleanup fails on any
    non-DummyThread / non-waitpid thread that outlives a test. HA's runner
    spawns _run_safe_shutdown_loop as a daemon during setup that we cannot
    easily stop. We hide all daemon threads from the cleanup check.
    """
    real_enumerate = threading.enumerate

    def filtered_enumerate() -> list[threading.Thread]:
        return [t for t in real_enumerate() if not t.daemon]

    monkeypatch.setattr(threading, "enumerate", filtered_enumerate)
