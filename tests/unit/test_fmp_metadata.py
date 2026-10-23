from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.services import stock_services


@pytest.mark.asyncio
async def test_resolve_symbol_returns_canonical_identity(monkeypatch):
    monkeypatch.setattr(
        stock_services,
        "make_fmp_request",
        AsyncMock(
            return_value=[
                {
                    "symbol": "NVDA",
                    "name": "NVIDIA Corporation",
                    "exchangeShortName": "NASDAQ",
                    "exchangeFullName": "NASDAQ Global Select",
                    "currency": "USD",
                }
            ]
        ),
    )

    result = await stock_services.resolve_symbol("nvda")

    assert result == {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "exchange": "NASDAQ",
        "exchange_full_name": "NASDAQ Global Select",
        "currency": "USD",
    }
