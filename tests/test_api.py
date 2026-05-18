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
