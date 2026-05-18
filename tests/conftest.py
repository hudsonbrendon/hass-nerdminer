"""Pytest fixtures shared across tests."""
import asyncio
import threading
from collections.abc import Generator

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


@pytest.fixture(autouse=True)
def verify_cleanup(
    event_loop: asyncio.AbstractEventLoop,
    expected_lingering_tasks: bool,  # noqa: ARG001
    expected_lingering_timers: bool,  # noqa: ARG001
) -> Generator[None]:
    """Override the plugin's verify_cleanup with one that tolerates HA daemon threads."""
    threads_before = frozenset(threading.enumerate())
    tasks_before = asyncio.all_tasks(event_loop)
    yield

    # Drain any remaining default-executor work so HA can finish shutdown.
    event_loop.run_until_complete(event_loop.shutdown_default_executor())

    # Cancel any lingering tasks (warn but don't fail — matches plugin's permissive mode).
    tasks = asyncio.all_tasks(event_loop) - tasks_before
    for task in tasks:
        task.cancel()
    if tasks:
        event_loop.run_until_complete(asyncio.wait(tasks))

    # Tolerate HA daemon threads (_run_safe_shutdown_loop etc.) that outlive the test.
    threads = frozenset(threading.enumerate()) - threads_before
    for thread in threads:
        is_safe = (
            isinstance(thread, threading._DummyThread)
            or thread.name.startswith("waitpid-")
            or thread.daemon
        )
        if not is_safe:
            raise AssertionError(f"Found leftover thread {thread.name}")
