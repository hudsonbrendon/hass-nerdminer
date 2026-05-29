# tests/test_api.py
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession

from custom_components.nerdminer.api import (
    NerdMinerApiClient,
    NerdMinerApiError,
    NerdMinerData,
)


@pytest.fixture
def sample_response():
    # Mirrors the real public-pool GET /api/client/:address response.
    return {
        "bestDifficulty": "4.057958877731942",
        "workersCount": 2,
        "workers": [
            {
                "sessionId": "abc123",
                "name": "nerdminer1",
                "bestDifficulty": "2.50",
                "hashRate": 78000,
                "startTime": "2026-05-17T10:00:00.000Z",
                "lastSeen": "2026-05-29T12:00:00.000Z",
            },
            {
                "sessionId": "def456",
                "name": "nerdminer2",
                "bestDifficulty": "1.10",
                "hashRate": 22000,
                "startTime": "2026-05-18T08:30:00.000Z",
                "lastSeen": "2026-05-29T12:00:05.000Z",
            },
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
    assert data.workers_count == 2
    assert len(data.workers) == 2

    worker = data.workers[0]
    assert worker.session_id == "abc123"
    assert worker.name == "nerdminer1"
    assert worker.hash_rate == 78000
    assert worker.best_difficulty == 2.5
    assert worker.start_time == "2026-05-17T10:00:00.000Z"
    assert worker.last_seen == "2026-05-29T12:00:00.000Z"

    worker2 = data.workers[1]
    assert worker2.session_id == "def456"
    assert worker2.name == "nerdminer2"
    assert worker2.hash_rate == 22000
    assert worker2.best_difficulty == 1.1


async def test_fetch_no_workers():
    session = AsyncMock(spec=ClientSession)
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value={
        "bestDifficulty": None,
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
