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
