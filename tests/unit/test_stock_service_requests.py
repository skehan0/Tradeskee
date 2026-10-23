from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException

from src.api.services import stock_services


class FakeResponse:
    def __init__(self, status_code, payload=None, json_error=False):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("invalid JSON")
        return self.payload


class FakeAsyncClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.get = AsyncMock(side_effect=self._get)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def _get(self, url):
        if self.error:
            raise self.error
        return self.response


@pytest.mark.asyncio
async def test_make_request_returns_json(monkeypatch):
    client = FakeAsyncClient(FakeResponse(200, {"price": "100"}))
    monkeypatch.setattr(stock_services.httpx, "AsyncClient", lambda **kwargs: client)

    result = await stock_services.make_request("https://provider.test", retries=1)

    assert result == {"price": "100"}
    client.get.assert_awaited_once_with("https://provider.test")


@pytest.mark.asyncio
async def test_make_request_retries_server_errors(monkeypatch):
    clients = [
        FakeAsyncClient(FakeResponse(503, {"error": "temporary"})),
        FakeAsyncClient(FakeResponse(200, {"ok": True})),
    ]
    monkeypatch.setattr(
        stock_services.httpx,
        "AsyncClient",
        lambda **kwargs: clients.pop(0),
    )
    sleep = AsyncMock()
    monkeypatch.setattr(stock_services.asyncio, "sleep", sleep)

    result = await stock_services.make_request(
        "https://provider.test", retries=2, backoff_factor=0
    )

    assert result == {"ok": True}
    sleep.assert_awaited_once_with(0)


@pytest.mark.asyncio
async def test_make_request_maps_rate_limit_to_429(monkeypatch):
    client = FakeAsyncClient(FakeResponse(429, {}))
    monkeypatch.setattr(stock_services.httpx, "AsyncClient", lambda **kwargs: client)

    with pytest.raises(HTTPException) as error:
        await stock_services.make_request("https://provider.test", retries=1)

    assert error.value.status_code == 429


@pytest.mark.asyncio
async def test_make_request_rejects_invalid_json(monkeypatch):
    client = FakeAsyncClient(FakeResponse(200, json_error=True))
    monkeypatch.setattr(stock_services.httpx, "AsyncClient", lambda **kwargs: client)

    with pytest.raises(HTTPException) as error:
        await stock_services.make_request("https://provider.test", retries=1)

    assert error.value.status_code == 502


@pytest.mark.asyncio
async def test_make_request_maps_provider_error(monkeypatch):
    client = FakeAsyncClient(FakeResponse(200, {"Error Message": "Invalid API call."}))
    monkeypatch.setattr(stock_services.httpx, "AsyncClient", lambda **kwargs: client)

    with pytest.raises(HTTPException) as error:
        await stock_services.make_request("https://provider.test", retries=1)

    assert error.value.status_code == 404
    assert error.value.detail == "Invalid API call."


@pytest.mark.asyncio
async def test_make_request_maps_network_failure(monkeypatch):
    client = FakeAsyncClient(error=httpx.ConnectError("connection failed"))
    monkeypatch.setattr(stock_services.httpx, "AsyncClient", lambda **kwargs: client)

    with pytest.raises(HTTPException) as error:
        await stock_services.make_request("https://provider.test", retries=1)

    assert error.value.status_code == 502
