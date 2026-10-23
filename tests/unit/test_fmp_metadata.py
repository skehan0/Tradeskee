from unittest.mock import AsyncMock, MagicMock

import pytest

from src.api.services import stock_services


@pytest.mark.asyncio
async def test_fmp_profile_maps_price_range_and_instrument_fields(monkeypatch):
    profile = {
        "symbol": "AAPL",
        "price": 331.85501,
        "marketCap": 4874072686740,
        "range": "201.5-344.57",
        "companyName": "Apple Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "exchangeFullName": "NASDAQ Global Select",
        "industry": "Consumer Electronics",
        "sector": "Technology",
        "description": "Apple Inc. is a global technology corporation.",
        "isEtf": False,
        "isFund": False,
        "isAdr": False,
        "isActivelyTrading": True,
    }
    database_handle = MagicMock()
    database_handle.stock_metadata.update_one = AsyncMock()

    monkeypatch.setattr(stock_services, "metadata_cache", {})
    monkeypatch.setattr(
        stock_services,
        "make_fmp_request",
        AsyncMock(
            side_effect=[
                [profile],
                [{"symbol": "AAPL", "price": 331.85501}],
            ]
        ),
    )
    monkeypatch.setattr(
        stock_services.database,
        "get_db",
        AsyncMock(return_value=database_handle),
    )

    result = await stock_services.fetch_stock_metadata("AAPL")

    assert result["name"] == "Apple Inc."
    assert result["current_price"] == 331.85501
    assert result["52_week_low"] == 201.5
    assert result["52_week_high"] == 344.57
    assert result["is_etf"] is False
    assert result["exchange_full_name"] == "NASDAQ Global Select"


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
