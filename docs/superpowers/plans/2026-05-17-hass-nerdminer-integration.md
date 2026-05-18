# Home Assistant NerdMiner Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HACS-installable Home Assistant integration that exposes NerdMiner V2 stats (hashrate, shares, best difficulty, online status) by polling the Public-Pool API.

**Architecture:** Standard HA custom integration with `DataUpdateCoordinator` polling pattern. Config flow lets users add their BTC address via UI. One coordinator per BTC address fans out to multiple sensor entities. No firmware modifications — purely API-driven.

**Tech Stack:** Python 3.12+, Home Assistant 2024.6+, `aiohttp` (HA built-in), `pytest`, `pytest-homeassistant-custom-component`, `voluptuous`, HACS metadata.

---

## File Structure

```
hass-nerdminer/
├── custom_components/
│   └── nerdminer/
│       ├── __init__.py              # Integration entry point, setup/unload
│       ├── manifest.json            # HA integration metadata
│       ├── const.py                 # Domain, defaults, API URL
│       ├── api.py                   # Async Public-Pool API client
│       ├── coordinator.py           # DataUpdateCoordinator subclass
│       ├── config_flow.py           # UI config + options flow
│       ├── sensor.py                # Sensor entities (hashrate, diff, shares)
│       ├── binary_sensor.py         # Online/offline binary sensor
│       ├── strings.json             # Source strings for UI
│       └── translations/
│           ├── en.json              # English translations
│           └── pt-BR.json           # Portuguese-BR translations
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures + HA setup
│   ├── test_api.py                  # API client unit tests
│   ├── test_coordinator.py          # Coordinator tests
│   ├── test_config_flow.py          # Config flow tests
│   ├── test_sensor.py               # Sensor entity tests
│   └── test_binary_sensor.py        # Binary sensor tests
├── hacs.json                        # HACS metadata
├── README.md                        # Installation + usage docs
├── LICENSE                          # MIT
├── pyproject.toml                   # Dev deps + ruff/mypy config
├── .gitignore
└── .github/
    └── workflows/
        ├── tests.yml                # CI: pytest on PR/push
        └── validate.yml             # HACS validation
```

**Why this structure:**
- `custom_components/nerdminer/` — required by HA + HACS conventions
- Module per concern (api/coordinator/config_flow/sensor) — each file one responsibility
- Tests mirror source structure
- HACS metadata at root for repo-level discovery

---

## Task 1: Project scaffold + dev environment

**Files:**
- Create: `~/nerdminer/hass-nerdminer/.gitignore`
- Create: `~/nerdminer/hass-nerdminer/pyproject.toml`
- Create: `~/nerdminer/hass-nerdminer/LICENSE`
- Create: `~/nerdminer/hass-nerdminer/.python-version`

- [ ] **Step 1: Init git repo and create base structure**

```bash
cd ~/nerdminer/hass-nerdminer
git init
mkdir -p custom_components/nerdminer/translations tests .github/workflows
```

- [ ] **Step 2: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
.venv/
venv/
*.egg-info/
dist/
build/
.DS_Store
.idea/
.vscode/
```

- [ ] **Step 3: Create pyproject.toml with dev tooling**

```toml
[project]
name = "hass-nerdminer"
version = "0.1.0"
description = "Home Assistant integration for NerdMiner V2 via Public-Pool API"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Hudson Brendon", email = "contato.hudsonbrendon@gmail.com" }]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "pytest-homeassistant-custom-component>=0.13.150",
    "homeassistant>=2024.6.0",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "A", "C4", "RET", "SIM", "ARG"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: Create LICENSE (MIT)**

```text
MIT License

Copyright (c) 2026 Hudson Brendon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 5: Install dev dependencies**

```bash
cd ~/nerdminer/hass-nerdminer
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: ~50 packages installed including `homeassistant`, `pytest-homeassistant-custom-component`.

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml LICENSE
git commit -m "chore: scaffold project with dev tooling"
```

---

## Task 2: Constants + manifest

**Files:**
- Create: `custom_components/nerdminer/const.py`
- Create: `custom_components/nerdminer/manifest.json`
- Test: `tests/test_const.py`

- [ ] **Step 1: Write failing test for constants**

```python
# tests/test_const.py
from custom_components.nerdminer.const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    API_BASE_URL,
    CONF_BTC_ADDRESS,
)


def test_domain():
    assert DOMAIN == "nerdminer"


def test_defaults():
    assert DEFAULT_SCAN_INTERVAL == 30
    assert API_BASE_URL == "https://public-pool.io:40557/api/client"
    assert CONF_BTC_ADDRESS == "btc_address"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_const.py -v`
Expected: FAIL with `ModuleNotFoundError: custom_components.nerdminer.const`

- [ ] **Step 3: Create const.py**

```python
# custom_components/nerdminer/const.py
"""Constants for the NerdMiner integration."""

DOMAIN = "nerdminer"
DEFAULT_SCAN_INTERVAL = 30  # seconds
API_BASE_URL = "https://public-pool.io:40557/api/client"
CONF_BTC_ADDRESS = "btc_address"
CONF_SCAN_INTERVAL = "scan_interval"

# Attribution shown in HA UI
ATTRIBUTION = "Data provided by Public-Pool"

# Entity keys (used as unique_id suffixes)
SENSOR_HASHRATE = "hashrate"
SENSOR_BEST_DIFFICULTY = "best_difficulty"
SENSOR_SESSION_ACCEPTED = "session_accepted"
SENSOR_SESSION_DIFFICULTY = "session_difficulty"
SENSOR_WORKERS_COUNT = "workers_count"
SENSOR_START_TIME = "start_time"
BINARY_SENSOR_ONLINE = "online"
```

- [ ] **Step 4: Need __init__.py for module imports — create empty stub**

```python
# custom_components/nerdminer/__init__.py
"""NerdMiner integration."""
```

Also create:
```python
# custom_components/__init__.py
```

And:
```python
# tests/__init__.py
```

- [ ] **Step 5: Run test to verify pass**

Run: `pytest tests/test_const.py -v`
Expected: PASS

- [ ] **Step 6: Create manifest.json**

```json
{
    "domain": "nerdminer",
    "name": "NerdMiner",
    "codeowners": ["@hudsonbrendon"],
    "config_flow": true,
    "dependencies": [],
    "documentation": "https://github.com/hudsonbrendon/hass-nerdminer",
    "integration_type": "service",
    "iot_class": "cloud_polling",
    "issue_tracker": "https://github.com/hudsonbrendon/hass-nerdminer/issues",
    "requirements": [],
    "version": "0.1.0"
}
```

- [ ] **Step 7: Commit**

```bash
git add custom_components tests/__init__.py tests/test_const.py
git commit -m "feat: add constants and manifest"
```

---

## Task 3: Async API client

**Files:**
- Create: `custom_components/nerdminer/api.py`
- Test: `tests/test_api.py`

**Design notes:**
- One method: `async fetch(address) -> NerdMinerData`
- Parses JSON into dataclass for type safety
- Raises `NerdMinerApiError` on network/parse errors
- Uses `aiohttp.ClientSession` injected by caller (HA provides one)
- Handles `workersCount: 0` (no active workers) gracefully — returns empty worker list, not error

- [ ] **Step 1: Write failing test — happy path**

```python
# tests/test_api.py
from unittest.mock import AsyncMock
import pytest
from aiohttp import ClientSession
from custom_components.nerdminer.api import (
    NerdMinerApiClient,
    NerdMinerApiError,
    NerdMinerData,
    WorkerData,
)


@pytest.fixture
def sample_response():
    return {
        "bestDifficulty": "4.057958877731942",
        "workersCount": 1,
        "workers": [
            {
                "sessionId": "abc123",
                "name": "nerdminer1",
                "hashRate": 78000,
                "startTime": "2026-05-17T10:00:00.000Z",
                "bestDifficulty": "2.5",
                "sessionDifficulty": 0.0016,
                "sessionAccepted": 42,
            }
        ],
    }


async def test_fetch_success(sample_response):
    session = AsyncMock(spec=ClientSession)
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=sample_response)
    session.get.return_value.__aenter__.return_value = resp

    client = NerdMinerApiClient(session)
    data = await client.fetch("bc1qtest")

    assert isinstance(data, NerdMinerData)
    assert data.best_difficulty == 4.057958877731942
    assert data.workers_count == 1
    assert len(data.workers) == 1
    worker = data.workers[0]
    assert worker.hash_rate == 78000
    assert worker.session_accepted == 42
    assert worker.session_difficulty == 0.0016


async def test_fetch_no_workers():
    session = AsyncMock(spec=ClientSession)
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={
        "bestDifficulty": "0",
        "workersCount": 0,
        "workers": [],
    })
    session.get.return_value.__aenter__.return_value = resp

    client = NerdMinerApiClient(session)
    data = await client.fetch("bc1qtest")

    assert data.workers_count == 0
    assert data.workers == []
    assert data.best_difficulty == 0.0


async def test_fetch_http_error():
    session = AsyncMock(spec=ClientSession)
    resp = AsyncMock()
    resp.status = 500
    session.get.return_value.__aenter__.return_value = resp

    client = NerdMinerApiClient(session)
    with pytest.raises(NerdMinerApiError):
        await client.fetch("bc1qtest")


async def test_fetch_network_error():
    import aiohttp
    session = AsyncMock(spec=ClientSession)
    session.get.side_effect = aiohttp.ClientError("connection refused")

    client = NerdMinerApiClient(session)
    with pytest.raises(NerdMinerApiError):
        await client.fetch("bc1qtest")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: custom_components.nerdminer.api`

- [ ] **Step 3: Implement API client**

```python
# custom_components/nerdminer/api.py
"""Public-Pool API client for NerdMiner integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import aiohttp

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class NerdMinerApiError(Exception):
    """Raised on API failures."""


@dataclass
class WorkerData:
    """Single worker stats."""

    session_id: str
    name: str
    hash_rate: float
    start_time: str
    best_difficulty: float
    session_difficulty: float
    session_accepted: int


@dataclass
class NerdMinerData:
    """Aggregated response from Public-Pool API."""

    best_difficulty: float
    workers_count: int
    workers: list[WorkerData] = field(default_factory=list)


class NerdMinerApiClient:
    """Async client for Public-Pool API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def fetch(self, btc_address: str) -> NerdMinerData:
        """Fetch stats for the given BTC address. Raises NerdMinerApiError on failure."""
        url = f"{API_BASE_URL}/{btc_address}"
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    raise NerdMinerApiError(f"HTTP {resp.status} from Public-Pool")
                payload: dict[str, Any] = await resp.json()
        except aiohttp.ClientError as err:
            raise NerdMinerApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise NerdMinerApiError("Timeout contacting Public-Pool") from err

        return self._parse(payload)

    @staticmethod
    def _parse(payload: dict[str, Any]) -> NerdMinerData:
        """Map raw API payload to typed dataclass."""
        workers = [
            WorkerData(
                session_id=w.get("sessionId", ""),
                name=w.get("name", ""),
                hash_rate=float(w.get("hashRate", 0)),
                start_time=w.get("startTime", ""),
                best_difficulty=float(w.get("bestDifficulty", 0) or 0),
                session_difficulty=float(w.get("sessionDifficulty", 0) or 0),
                session_accepted=int(w.get("sessionAccepted", 0) or 0),
            )
            for w in payload.get("workers", [])
        ]
        return NerdMinerData(
            best_difficulty=float(payload.get("bestDifficulty", 0) or 0),
            workers_count=int(payload.get("workersCount", 0) or 0),
            workers=workers,
        )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_api.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/nerdminer/api.py tests/test_api.py
git commit -m "feat: add async Public-Pool API client"
```

---

## Task 4: DataUpdateCoordinator

**Files:**
- Create: `custom_components/nerdminer/coordinator.py`
- Test: `tests/test_coordinator.py`

**Design notes:**
- Subclass `DataUpdateCoordinator[NerdMinerData]`
- Wraps `NerdMinerApiClient`, stores BTC address
- `update_interval` configurable via entry options (default 30s)
- Translates `NerdMinerApiError` → `UpdateFailed` (HA semantics)

- [ ] **Step 1: Write failing test**

```python
# tests/test_coordinator.py
from unittest.mock import AsyncMock, MagicMock
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.nerdminer.api import NerdMinerApiError, NerdMinerData
from custom_components.nerdminer.coordinator import NerdMinerCoordinator


async def test_coordinator_success(hass):
    api = AsyncMock()
    api.fetch.return_value = NerdMinerData(
        best_difficulty=1.5, workers_count=1, workers=[]
    )
    coord = NerdMinerCoordinator(hass, api, "bc1qtest", scan_interval=30)

    data = await coord._async_update_data()

    assert data.best_difficulty == 1.5
    api.fetch.assert_awaited_once_with("bc1qtest")


async def test_coordinator_api_failure_raises_update_failed(hass):
    api = AsyncMock()
    api.fetch.side_effect = NerdMinerApiError("boom")
    coord = NerdMinerCoordinator(hass, api, "bc1qtest", scan_interval=30)

    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_coordinator_interval_configurable(hass):
    api = AsyncMock()
    coord = NerdMinerCoordinator(hass, api, "bc1qtest", scan_interval=120)
    assert coord.update_interval.total_seconds() == 120
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_coordinator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create conftest.py for HA fixtures**

```python
# tests/conftest.py
"""Pytest fixtures shared across tests."""
import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of custom_components for all tests."""
    yield
```

- [ ] **Step 4: Implement coordinator**

```python
# custom_components/nerdminer/coordinator.py
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
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_coordinator.py -v`
Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
git add custom_components/nerdminer/coordinator.py tests/test_coordinator.py tests/conftest.py
git commit -m "feat: add DataUpdateCoordinator"
```

---

## Task 5: Config flow (UI setup)

**Files:**
- Create: `custom_components/nerdminer/config_flow.py`
- Create: `custom_components/nerdminer/strings.json`
- Create: `custom_components/nerdminer/translations/en.json`
- Create: `custom_components/nerdminer/translations/pt-BR.json`
- Test: `tests/test_config_flow.py`

**Design notes:**
- User submits BTC address; flow validates by hitting API once
- Prevents duplicate entries by using `btc_address` as unique_id
- Options flow lets user change `scan_interval` post-setup

- [ ] **Step 1: Write failing tests for config flow**

```python
# tests/test_config_flow.py
from unittest.mock import AsyncMock, patch
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from custom_components.nerdminer.const import (
    DOMAIN,
    CONF_BTC_ADDRESS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from custom_components.nerdminer.api import NerdMinerApiError, NerdMinerData


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
            {CONF_BTC_ADDRESS: "bc1qtestaddress12345"},
        )
        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "NerdMiner (bc1qtestad…)"
        assert result["data"] == {CONF_BTC_ADDRESS: "bc1qtestaddress12345"}


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
            {CONF_BTC_ADDRESS: "bc1qtestaddress12345"},
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
        data={CONF_BTC_ADDRESS: "bc1qtestaddress12345"},
        source=config_entries.SOURCE_USER,
        options={},
        unique_id="bc1qtestaddress12345",
        discovery_keys={},
    )
    hass.config_entries._entries[entry.entry_id] = entry

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60}
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_SCAN_INTERVAL: 60}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config_flow.py -v`
Expected: FAIL — config_flow not yet implemented

- [ ] **Step 3: Implement config flow**

```python
# custom_components/nerdminer/config_flow.py
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
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlow:
        return NerdMinerOptionsFlow(config_entry)


class NerdMinerOptionsFlow(OptionsFlow):
    """Options flow for adjusting scan interval."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

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
```

- [ ] **Step 4: Create strings.json**

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Add NerdMiner",
                "description": "Enter your Bitcoin payout address to track mining stats from Public-Pool.",
                "data": {
                    "btc_address": "Bitcoin address"
                }
            }
        },
        "error": {
            "cannot_connect": "Failed to reach Public-Pool API.",
            "invalid_address": "That doesn't look like a valid Bitcoin address."
        },
        "abort": {
            "already_configured": "This Bitcoin address is already configured."
        }
    },
    "options": {
        "step": {
            "init": {
                "title": "NerdMiner options",
                "data": {
                    "scan_interval": "Scan interval (seconds)"
                }
            }
        }
    }
}
```

- [ ] **Step 5: Create translations/en.json (copy of strings.json)**

```bash
cp custom_components/nerdminer/strings.json custom_components/nerdminer/translations/en.json
```

- [ ] **Step 6: Create translations/pt-BR.json**

```json
{
    "config": {
        "step": {
            "user": {
                "title": "Adicionar NerdMiner",
                "description": "Informe seu endereço Bitcoin para acompanhar estatísticas no Public-Pool.",
                "data": {
                    "btc_address": "Endereço Bitcoin"
                }
            }
        },
        "error": {
            "cannot_connect": "Falha ao contatar API do Public-Pool.",
            "invalid_address": "Endereço Bitcoin inválido."
        },
        "abort": {
            "already_configured": "Endereço Bitcoin já configurado."
        }
    },
    "options": {
        "step": {
            "init": {
                "title": "Opções do NerdMiner",
                "data": {
                    "scan_interval": "Intervalo de atualização (segundos)"
                }
            }
        }
    }
}
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_config_flow.py -v`
Expected: 4 PASS

- [ ] **Step 8: Commit**

```bash
git add custom_components/nerdminer/config_flow.py custom_components/nerdminer/strings.json custom_components/nerdminer/translations tests/test_config_flow.py
git commit -m "feat: add config flow with BTC address validation"
```

---

## Task 6: Integration setup/unload (__init__.py)

**Files:**
- Modify: `custom_components/nerdminer/__init__.py`
- Test: `tests/test_init.py`

**Design notes:**
- `async_setup_entry`: create coordinator, store in `hass.data[DOMAIN][entry_id]`, forward to platforms
- `async_unload_entry`: pop coordinator, unload platforms
- Reload entry when options change (so new scan_interval takes effect)

- [ ] **Step 1: Write failing test**

```python
# tests/test_init.py
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.nerdminer.const import (
    DOMAIN,
    CONF_BTC_ADDRESS,
    CONF_SCAN_INTERVAL,
)
from custom_components.nerdminer.api import NerdMinerData


async def test_setup_and_unload(hass: HomeAssistant):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_BTC_ADDRESS: "bc1qtest"},
        options={CONF_SCAN_INTERVAL: 30},
        unique_id="bc1qtest",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.nerdminer.coordinator.NerdMinerApiClient.fetch",
        AsyncMock(return_value=NerdMinerData(best_difficulty=0, workers_count=0, workers=[])),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]

        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.entry_id not in hass.data.get(DOMAIN, {})
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_init.py -v`
Expected: FAIL — setup not yet implemented

- [ ] **Step 3: Implement __init__.py**

```python
# custom_components/nerdminer/__init__.py
"""NerdMiner integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NerdMinerApiClient
from .const import CONF_BTC_ADDRESS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import NerdMinerCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NerdMiner from a config entry."""
    session = async_get_clientsession(hass)
    api = NerdMinerApiClient(session)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = NerdMinerCoordinator(
        hass, api, entry.data[CONF_BTC_ADDRESS], scan_interval
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change so new scan_interval takes effect."""
    await hass.config_entries.async_reload(entry.entry_id)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_init.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/nerdminer/__init__.py tests/test_init.py
git commit -m "feat: add integration setup/unload with coordinator wiring"
```

---

## Task 7: Sensor platform

**Files:**
- Create: `custom_components/nerdminer/sensor.py`
- Test: `tests/test_sensor.py`

**Design notes:**
- Six sensors: hashrate, best_difficulty, session_accepted, session_difficulty, workers_count, start_time
- All inherit `CoordinatorEntity[NerdMinerCoordinator]` + `SensorEntity`
- Use `SensorEntityDescription` for declarative config
- Sensors that depend on a worker (hashrate etc.) return `None` when no workers

- [ ] **Step 1: Write failing tests**

```python
# tests/test_sensor.py
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.nerdminer.const import DOMAIN, CONF_BTC_ADDRESS
from custom_components.nerdminer.api import NerdMinerData, WorkerData


async def _setup_with(hass: HomeAssistant, data: NerdMinerData):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_BTC_ADDRESS: "bc1qtest"},
        unique_id="bc1qtest",
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.nerdminer.coordinator.NerdMinerApiClient.fetch",
        AsyncMock(return_value=data),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_sensors_with_active_worker(hass: HomeAssistant):
    worker = WorkerData(
        session_id="s1",
        name="nerdminer1",
        hash_rate=78000,
        start_time="2026-05-17T10:00:00.000Z",
        best_difficulty=2.5,
        session_difficulty=0.0016,
        session_accepted=42,
    )
    data = NerdMinerData(best_difficulty=4.06, workers_count=1, workers=[worker])
    await _setup_with(hass, data)

    assert hass.states.get("sensor.nerdminer_bc1qtest_hashrate").state == "78.0"
    assert hass.states.get("sensor.nerdminer_bc1qtest_best_difficulty").state == "4.06"
    assert hass.states.get("sensor.nerdminer_bc1qtest_session_accepted").state == "42"
    assert hass.states.get("sensor.nerdminer_bc1qtest_session_difficulty").state == "0.0016"
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "1"


async def test_sensors_no_worker_returns_none(hass: HomeAssistant):
    data = NerdMinerData(best_difficulty=0, workers_count=0, workers=[])
    await _setup_with(hass, data)

    state = hass.states.get("sensor.nerdminer_bc1qtest_hashrate")
    assert state.state in ("unknown", "0", "0.0")
    assert hass.states.get("sensor.nerdminer_bc1qtest_workers_count").state == "0"
```

- [ ] **Step 2: Run tests to verify fail**

Run: `pytest tests/test_sensor.py -v`
Expected: FAIL — sensor.py not yet implemented

- [ ] **Step 3: Implement sensor platform**

```python
# custom_components/nerdminer/sensor.py
"""Sensor platform for NerdMiner."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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


def _first_worker_attr(attr: str, *, scale: float = 1.0):
    def _get(data: NerdMinerData) -> float | int | None:
        if not data.workers:
            return None
        return getattr(data.workers[0], attr) * scale
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
        name="Session shares accepted",
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
        name="Workers",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.workers_count,
    ),
    NerdMinerSensorDescription(
        key=SENSOR_START_TIME,
        translation_key=SENSOR_START_TIME,
        name="Session start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_first_worker_attr("start_time"),
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_sensor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/nerdminer/sensor.py tests/test_sensor.py
git commit -m "feat: add sensor platform with 6 sensors"
```

---

## Task 8: Binary sensor (online status)

**Files:**
- Create: `custom_components/nerdminer/binary_sensor.py`
- Test: `tests/test_binary_sensor.py`

**Design notes:**
- Single binary sensor: `online`
- `is_on` true when `workers_count > 0`
- `device_class` = `connectivity`

- [ ] **Step 1: Write failing test**

```python
# tests/test_binary_sensor.py
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.nerdminer.const import DOMAIN, CONF_BTC_ADDRESS
from custom_components.nerdminer.api import NerdMinerData, WorkerData


async def _setup(hass, data):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_BTC_ADDRESS: "bc1qtest"},
        unique_id="bc1qtest",
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.nerdminer.coordinator.NerdMinerApiClient.fetch",
        AsyncMock(return_value=data),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


async def test_online_when_worker_active(hass: HomeAssistant):
    worker = WorkerData(
        session_id="s", name="w", hash_rate=1, start_time="",
        best_difficulty=0, session_difficulty=0, session_accepted=0,
    )
    await _setup(hass, NerdMinerData(best_difficulty=0, workers_count=1, workers=[worker]))
    state = hass.states.get("binary_sensor.nerdminer_bc1qtest_online")
    assert state.state == "on"


async def test_offline_when_no_workers(hass: HomeAssistant):
    await _setup(hass, NerdMinerData(best_difficulty=0, workers_count=0, workers=[]))
    state = hass.states.get("binary_sensor.nerdminer_bc1qtest_online")
    assert state.state == "off"
```

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_binary_sensor.py -v`
Expected: FAIL — module missing

- [ ] **Step 3: Implement binary_sensor.py**

```python
# custom_components/nerdminer/binary_sensor.py
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
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_binary_sensor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/nerdminer/binary_sensor.py tests/test_binary_sensor.py
git commit -m "feat: add online binary sensor"
```

---

## Task 9: HACS metadata + README

**Files:**
- Create: `hacs.json`
- Create: `README.md`

- [ ] **Step 1: Create hacs.json**

```json
{
    "name": "NerdMiner",
    "render_readme": true,
    "homeassistant": "2024.6.0",
    "country": ["BR", "US"]
}
```

- [ ] **Step 2: Create README.md**

````markdown
# NerdMiner — Home Assistant Integration

Track your [NerdMiner V2](https://github.com/BitMaker-hub/NerdMiner_v2) solo Bitcoin miner stats in Home Assistant via the [Public-Pool](https://web.public-pool.io) API.

## Features

- Hashrate (kH/s)
- Session shares accepted
- Best difficulty (chance of finding a block)
- Workers count
- Session start time
- Online/offline binary sensor

## Installation

### HACS (recommended)

1. Add this repo as a custom repository in HACS (Integrations → ⋮ → Custom repositories).
2. Search "NerdMiner" → Download.
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → "NerdMiner".

### Manual

```bash
cd ~/.homeassistant
git clone https://github.com/hudsonbrendon/hass-nerdminer
cp -r hass-nerdminer/custom_components/nerdminer custom_components/
```

Restart HA and add the integration via Settings.

## Configuration

You only need your **Bitcoin payout address** (the one configured on the miner). Example: `bc1qddj…`

## Sensors created

| Entity | Description |
|--------|-------------|
| `sensor.nerdminer_<addr>_hashrate` | Current hashrate (kH/s) |
| `sensor.nerdminer_<addr>_best_difficulty` | Best difficulty ever found by this address |
| `sensor.nerdminer_<addr>_session_accepted` | Shares accepted this session |
| `sensor.nerdminer_<addr>_session_difficulty` | Current pool difficulty |
| `sensor.nerdminer_<addr>_workers_count` | Active workers |
| `sensor.nerdminer_<addr>_session_start` | Session start timestamp |
| `binary_sensor.nerdminer_<addr>_online` | True when at least one worker is reporting |

## Example automations

### Notify on block found (lottery!)

```yaml
automation:
  - alias: "NerdMiner — block found"
    trigger:
      - platform: numeric_state
        entity_id: sensor.nerdminer_<addr>_best_difficulty
        above: 100000000
    action:
      - service: notify.mobile_app_phone
        data:
          title: "Bitcoin block found!"
          message: "Difficulty: {{ trigger.to_state.state }}"
```

### Alert when offline

```yaml
automation:
  - alias: "NerdMiner — offline alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.nerdminer_<addr>_online
        to: "off"
        for: "00:10:00"
    action:
      - service: notify.mobile_app_phone
        data:
          message: "Miner offline for 10 minutes."
```

## Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## License

MIT
````

- [ ] **Step 3: Commit**

```bash
git add hacs.json README.md
git commit -m "docs: add HACS metadata and README"
```

---

## Task 10: GitHub Actions CI

**Files:**
- Create: `.github/workflows/tests.yml`
- Create: `.github/workflows/validate.yml`

- [ ] **Step 1: Create tests.yml**

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -e ".[dev]"
      - run: ruff check custom_components tests
      - run: pytest -v --cov=custom_components.nerdminer --cov-report=term-missing
```

- [ ] **Step 2: Create validate.yml (HACS validation)**

```yaml
name: validate

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 0 * * *"

jobs:
  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: HACS validation
        uses: hacs/action@main
        with:
          category: integration
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows
git commit -m "ci: add tests and HACS validation workflows"
```

---

## Task 11: End-to-end smoke test

**Files:**
- No new files. Manual verification.

- [ ] **Step 1: Run full test suite**

```bash
cd ~/nerdminer/hass-nerdminer
source .venv/bin/activate
pytest -v --cov=custom_components.nerdminer
```

Expected: All tests PASS, coverage > 85%.

- [ ] **Step 2: Run linting**

```bash
ruff check custom_components tests
mypy custom_components/nerdminer
```

Expected: zero errors.

- [ ] **Step 3: Run hassfest locally (validates manifest, translations, etc.)**

```bash
docker run --rm -v "$PWD:/github/workspace" ghcr.io/home-assistant/hassfest:latest
```

Expected: no issues reported.

- [ ] **Step 4: Live test against a running HA**

Pre-req: an HA instance (HAOS, container, or `hass --debug` from venv).

1. Copy `custom_components/nerdminer/` into the HA config dir.
2. Restart HA.
3. UI → Settings → Devices & Services → Add Integration → "NerdMiner".
4. Enter the real BTC address (`bc1qddjxw3ay8yhl0d5a6l8qn8ucdx649et8qkec02`).
5. Verify all 6 sensors + 1 binary sensor appear under a "NerdMiner" device.
6. Verify states update within 30s of mining activity.

- [ ] **Step 5: Push to GitHub and tag v0.1.0**

```bash
git remote add origin git@github.com:hudsonbrendon/hass-nerdminer.git
git branch -M main
git push -u origin main
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

- [ ] **Step 6: Create GitHub release**

GitHub → Releases → Draft new release → tag `v0.1.0` → title "v0.1.0" → describe features → Publish.

This triggers HACS to discover the release.

---

## Self-review checklist

- **Spec coverage:**
  - Public-Pool API only ✓ (Task 3)
  - HACS-ready distribution ✓ (Tasks 9, 11)
  - All 6 sensor types from spec ✓ (Task 7)
  - Online status binary sensor ✓ (Task 8)
- **No placeholders:** every code block is concrete and complete.
- **Type consistency:** `NerdMinerData`/`WorkerData` field names match across api.py, coordinator.py, sensor.py, binary_sensor.py.
- **Frequent commits:** each task ends with a commit. 11 commits total.
