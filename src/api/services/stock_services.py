import asyncio
import logging
import time
from datetime import UTC, datetime

import httpx
from cachetools import TTLCache
from fastapi import HTTPException

from src.api.models.stock_models import StockHistoricalData, StockMetadata
from src.core.config import settings
from src.infrastructure.database.mongoDB.database import database

API_KEY = settings.ALPHA_VANTAGE_API_KEY

# Caches with a TTL of 1 hour and a max size of 100 items
metadata_cache = TTLCache(maxsize=100, ttl=3600)
historical_data_cache = TTLCache(maxsize=100, ttl=3600)
news_cache = TTLCache(maxsize=100, ttl=3600)
income_statement_cache = TTLCache(maxsize=100, ttl=3600)
balance_sheet_cache = TTLCache(maxsize=100, ttl=3600)
cash_flow_cache = TTLCache(maxsize=100, ttl=3600)
earnings_cache = TTLCache(maxsize=100, ttl=3600)
sma_cache = TTLCache(maxsize=100, ttl=3600)
ema_cache = TTLCache(maxsize=100, ttl=3600)
top_gainers_losers_cache = TTLCache(maxsize=100, ttl=3600)
market_data_cache = {"data": {}, "last_updated": 0}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Helper function for API requests with retries
async def make_request(url: str, retries: int = 3, backoff_factor: float = 0.5):
    """
    Fetch JSON from an upstream provider with bounded retries.
    """
    for attempt in range(retries):
        try:
            timeout = httpx.Timeout(settings.ALPHA_VANTAGE_TIMEOUT)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
        except httpx.RequestError as error:
            if attempt < retries - 1:
                await asyncio.sleep(backoff_factor * (2**attempt))
                continue
            raise HTTPException(
                status_code=502,
                detail="Unable to reach the market data provider.",
            ) from error

        retryable = response.status_code >= 500
        if retryable and attempt < retries - 1:
            await asyncio.sleep(backoff_factor * (2**attempt))
            continue

        if response.status_code == 429:
            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch data from the market data provider.",
            )

        try:
            data = response.json()
        except ValueError as error:
            raise HTTPException(
                status_code=502,
                detail="Market data provider returned invalid JSON.",
            ) from error

        if "Error Message" in data:
            raise HTTPException(status_code=404, detail=data["Error Message"])
        if "Note" in data:
            raise HTTPException(status_code=429, detail=data["Note"])
        if "Information" in data:
            information = data["Information"]
            information_lower = information.lower()
            if any(
                phrase in information_lower
                for phrase in (
                    "rate limit",
                    "requests per second",
                    "requests per day",
                    "free key",
                    "spread out your free api requests",
                )
            ):
                raise HTTPException(status_code=429, detail=information)
            raise HTTPException(status_code=503, detail=information)
        return data

    raise HTTPException(
        status_code=502, detail="Market data provider failed after multiple attempts."
    )


async def make_fmp_request(path: str, params: dict[str, str | int]) -> object:
    """Fetch a JSON response from FMP using header-based authentication."""
    if not settings.FMP_API_KEY:
        raise HTTPException(
            status_code=503, detail="Financial Modeling Prep API key is not configured."
        )

    for attempt in range(3):
        try:
            timeout = httpx.Timeout(settings.ALPHA_VANTAGE_TIMEOUT)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{settings.FMP_BASE_URL}{path}",
                    params=params,
                    headers={"apikey": settings.FMP_API_KEY},
                )
        except httpx.RequestError as error:
            if attempt < 2:
                await asyncio.sleep(0.5 * (2**attempt))
                continue
            raise HTTPException(
                status_code=502, detail="Unable to reach the FMP provider."
            ) from error

        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="FMP rate limit exceeded.")
        if response.status_code >= 500 and attempt < 2:
            await asyncio.sleep(0.5 * (2**attempt))
            continue
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="FMP provider request failed.")

        try:
            data = response.json()
        except ValueError as error:
            raise HTTPException(
                status_code=502, detail="FMP provider returned invalid JSON."
            ) from error

        if isinstance(data, dict) and any(
            key in data for key in ("Error Message", "error", "Error")
        ):
            raise HTTPException(
                status_code=502, detail="FMP provider returned an error."
            )
        return data

    raise HTTPException(status_code=502, detail="FMP provider failed after retries.")


async def resolve_symbol(ticker: str) -> dict:
    """Resolve a ticker through FMP before requesting security data."""
    data = await make_fmp_request("/search-symbol", {"query": ticker})
    if not isinstance(data, list) or not data:
        raise HTTPException(
            status_code=404, detail=f"No security was found for ticker {ticker}."
        )

    matches = [
        item for item in data if str(item.get("symbol", "")).upper() == ticker.upper()
    ]
    match = matches[0] if matches else data[0]
    return {
        "ticker": str(match.get("symbol", ticker)).upper(),
        "name": match.get("name") or match.get("companyName"),
        "exchange": match.get("exchangeShortName") or match.get("exchange"),
        "exchange_full_name": match.get("exchangeFullName"),
        "currency": match.get("currency"),
    }


async def fetch_current_quote(ticker: str) -> dict:
    """Fetch the latest quote from FMP."""
    data = await make_fmp_request("/quote", {"symbol": ticker})
    if not isinstance(data, list) or not data:
        raise HTTPException(status_code=502, detail="FMP returned no quote data.")
    return data[0]


async def fetch_all_stock_data(ticker: str):
    """
    Fetch all relevant stock data by calling multiple endpoints.
    """
    try:
        resolved = await resolve_symbol(ticker)
        ticker = resolved["ticker"]
        # Step 1: Fetch metadata
        metadata = await fetch_stock_metadata(ticker)
        metadata["resolution"] = resolved

        # Step 2: Fetch historical data
        historical_data = await fetch_historical_data(ticker)

        # Step 3: Fetch news headlines
        try:
            news = await fetch_news_headlines(ticker)
            news_status = "available" if news else "unavailable"
        except HTTPException as error:
            logger.warning("News unavailable for %s: %s", ticker, error.detail)
            news = []
            news_status = "unavailable"

        # Step 4: Fetch income statement
        income_statement = await fetch_income_statement(ticker)

        # Step 5: Fetch balance sheet
        balance_sheet = await fetch_balance_sheet(ticker)

        # Step 6: Fetch cash flow
        cash_flow = await fetch_cash_flow(ticker)

        # Step 7: Fetch earnings
        earnings = await fetch_earnings(ticker)

        metrics = await fetch_financial_metrics(ticker)

        # Step 8: Fetch SMA (Simple Moving Average)
        sma = await fetch_SMA(ticker)

        # Step 9: Fetch EMA (Exponential Moving Average)
        ema = await fetch_EMA(ticker)

        # Step 10: Consolidate the analysis datasets
        consolidated_data = {
            "metadata": metadata,
            "historical_data": historical_data,
            "news": news,
            "news_status": news_status,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "earnings": earnings,
            "financial_metrics": metrics,
            "sma": sma,
            "ema": ema,
        }

        return consolidated_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch all stock data for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch all stock data: {str(e)}"
        )


# Specific Data Calls
async def fetch_stock_metadata(ticker: str):
    """
    Fetching stock metadata of a specific ticker input symbol
    """
    if ticker in metadata_cache:
        return metadata_cache[ticker]

    if not settings.FMP_API_KEY:
        raise HTTPException(
            status_code=503, detail="Financial Modeling Prep API key is not configured."
        )

    data = await make_fmp_request("/profile", {"symbol": ticker})
    if not isinstance(data, list) or not data:
        raise HTTPException(
            status_code=502,
            detail="Financial Modeling Prep returned no company profile data.",
        )
    profile = data[0]
    quote = await fetch_current_quote(ticker)
    price_range = profile.get("range", "")
    range_low = None
    range_high = None
    if isinstance(price_range, str) and "-" in price_range:
        low_value, high_value = price_range.split("-", 1)
        try:
            range_low = float(low_value)
            range_high = float(high_value)
        except ValueError:
            logger.warning("Invalid FMP price range for %s: %s", ticker, price_range)
    db = await database.get_db()

    metadata = {
        "ticker": ticker,
        "name": profile.get("companyName"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "market_cap": profile.get("marketCap"),
        "dividend_yield": profile.get("lastDividend"),
        "pe_ratio": None,
        "eps": None,
        "beta": profile.get("beta"),
        "52_week_high": range_high,
        "52_week_low": range_low,
        "current_price": quote.get("price", profile.get("price")),
        "change": quote.get("change"),
        "change_percentage": quote.get("changePercentage"),
        "volume": quote.get("volume"),
        "quote_timestamp": quote.get("timestamp"),
        "analyst_ratings": None,
        "price_targets": None,
        "events": None,
        "description": profile.get("description"),
        "exchange": profile.get("exchange"),
        "exchange_full_name": profile.get("exchangeFullName"),
        "currency": profile.get("currency"),
        "is_etf": profile.get("isEtf", False),
        "is_fund": profile.get("isFund", False),
        "is_adr": profile.get("isAdr", False),
        "is_actively_trading": profile.get("isActivelyTrading"),
        "last_updated": datetime.now(UTC),
    }

    # Store in MongoDB (overwrite existing data)
    await db.stock_metadata.update_one(
        {"ticker": ticker}, {"$set": metadata}, upsert=True
    )
    logger.info(f"Stored metadata for {ticker} in database")

    # Update cache
    metadata_cache[ticker] = metadata

    return metadata


async def fetch_historical_data(ticker: str, limit: int = 5):
    """
    Fetch weekly historical stock data with a limit on the number of entries.
    """
    if ticker in historical_data_cache:
        # Return limited data from the cache
        cached_data = historical_data_cache[ticker].copy()
        cached_data["historical_data"] = cached_data["historical_data"][:limit]
        return cached_data

    # Check if historical data is already stored in the database
    db = await database.get_db()
    existing_data = await db.historical_data.find_one({"ticker": ticker})
    if existing_data:
        existing_data["_id"] = str(existing_data["_id"])
        # Limit the number of entries
        existing_data["historical_data"] = existing_data["historical_data"][:limit]
        return existing_data

    try:
        data = await make_fmp_request(
            "/historical-price-eod/full", {"symbol": ticker, "limit": limit}
        )
        if not isinstance(data, list):
            raise HTTPException(
                status_code=502, detail="FMP returned no price history."
            )

        cleaned_data = [
            {
                "date": item.get("date"),
                "open": item.get("open"),
                "high": item.get("high"),
                "low": item.get("low"),
                "close": item.get("close"),
                "adjusted_close": item.get("adjClose", item.get("close")),
                "volume": item.get("volume"),
                "vwap": item.get("vwap"),
            }
            for item in data
            if item.get("date")
            and all(
                item.get(field) is not None
                for field in ("open", "high", "low", "close", "volume")
            )
        ][
            :limit
        ]  # Apply the limit here

        historical_data = {
            "ticker": ticker,
            "historical_data": cleaned_data,
            "last_updated": datetime.now(UTC),
        }

        if cleaned_data:
            await db.historical_data.update_one(
                {"ticker": ticker}, {"$set": historical_data}, upsert=True
            )
            logger.info(f"Stored historical data for {ticker} in database")
            historical_data_cache[ticker] = historical_data

        return historical_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch historical data: {str(e)}"
        )


# Fetch news headlines
async def fetch_news_headlines(ticker: str, limit: int = 3):
    """
    Stock news for specific ticker input
    """
    cache_key = f"{ticker}_{limit}"
    if cache_key in news_cache:
        return news_cache[cache_key]

    data = await make_fmp_request(
        "/news/stock", {"symbols": ticker, "page": 0, "limit": limit}
    )
    news_data = data if isinstance(data, list) else []

    cleaned_news = [
        {
            "article": index + 1,
            "title": item.get("title", "N/A"),
            "summary": item.get("text", "N/A"),
            "pubDate": item.get("publishedDate", "N/A"),
            "url": item.get("url", "N/A"),
            "thumbnail": item.get("image", "N/A"),
            "sentimentScore": None,
            "sentimentLabel": "N/A",
        }
        for index, item in enumerate(news_data[:limit])
    ]

    # Cache the result
    news_cache[cache_key] = cleaned_news
    return cleaned_news


# Fetch fetchLiveNewsHeadlines
async def fetch_live_news_headlines(limit: int = 3):
    """
    Fetching live market news for the frontend, no specific stock ticker
    """
    cache_key = f"{limit}"
    if cache_key in news_cache:
        return news_cache[cache_key]

    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={API_KEY}"
    data = await make_request(url)
    news_data = data.get("feed", [])

    cleaned_news = [
        {
            "article": index + 1,
            "title": item.get("title", "N/A"),
            "summary": item.get("summary", "N/A"),
            "pubDate": item.get("time_published", "N/A"),
            "url": item.get("url", "N/A"),
            "thumbnail": item.get("banner_image", "N/A"),
            "sentimentScore": item.get("overall_sentiment_score", "N/A"),
            "sentimentLabel": item.get("overall_sentiment_label", "N/A"),
        }
        for index, item in enumerate(news_data[:limit])
    ]

    result = {"news": cleaned_news}
    news_cache[cache_key] = result
    return result


# Fetch Income Statement
async def fetch_income_statement(ticker: str, limit: int = 1):
    cache_key = f"{ticker}_{limit}"
    if cache_key in income_statement_cache:
        return income_statement_cache[cache_key]

    # Check if income statement is already stored in the database
    db = await database.get_db()
    existing_income_statement = await db.income_statement.find_one({"ticker": ticker})
    if existing_income_statement:
        existing_income_statement["_id"] = str(existing_income_statement["_id"])
        return existing_income_statement

    data = await make_fmp_request(
        "/income-statement", {"symbol": ticker, "limit": limit}
    )
    if not isinstance(data, list):
        raise HTTPException(
            status_code=502, detail="FMP returned no income statements."
        )

    # Process the data to limit the number of statements
    limited_data = {
        "ticker": ticker,
        "annual_reports": data[:limit],
    }

    if limited_data["annual_reports"]:
        await db.income_statement.update_one(
            {"ticker": ticker}, {"$set": limited_data}, upsert=True
        )
        logger.info(f"Stored income statement for {ticker} in database")

    # Cache the result
    income_statement_cache[cache_key] = limited_data

    return limited_data


# Fetch Balance Sheet
async def fetch_balance_sheet(ticker: str, limit: int = 1):
    cache_key = f"{ticker}_{limit}"
    if cache_key in balance_sheet_cache:
        return balance_sheet_cache[cache_key]

    # Check if balance sheet is already stored in the database
    db = await database.get_db()
    existing_balance_sheet = await db.balance_sheet.find_one({"ticker": ticker})
    if existing_balance_sheet:
        existing_balance_sheet["_id"] = str(existing_balance_sheet["_id"])
        return existing_balance_sheet

    data = await make_fmp_request(
        "/balance-sheet-statement", {"symbol": ticker, "limit": limit}
    )
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="FMP returned no balance sheets.")

    # Process the data to limit the number of balance sheets
    limited_data = {
        "ticker": ticker,
        "annual_reports": data[:limit],
    }

    if limited_data["annual_reports"]:
        await db.balance_sheet.update_one(
            {"ticker": ticker}, {"$set": limited_data}, upsert=True
        )
        logger.info(f"Stored balance sheet for {ticker} in database")

    # Cache the result
    balance_sheet_cache[cache_key] = limited_data

    return limited_data


# Fetch Cash Flow
async def fetch_cash_flow(ticker: str, limit: int = 1):
    cache_key = f"{ticker}_{limit}"
    if cache_key in cash_flow_cache:
        return cash_flow_cache[cache_key]

    # Check if cash flow is already stored in the database
    db = await database.get_db()
    existing_cash_flow = await db.cash_flow.find_one({"ticker": ticker})
    if existing_cash_flow:
        existing_cash_flow["_id"] = str(existing_cash_flow["_id"])
        return existing_cash_flow

    data = await make_fmp_request(
        "/cash-flow-statement", {"symbol": ticker, "limit": limit}
    )
    if not isinstance(data, list):
        raise HTTPException(
            status_code=502, detail="FMP returned no cash-flow statements."
        )

    # Process the data to limit the number of cash flows
    limited_data = {
        "ticker": ticker,
        "annual_reports": data[:limit],
    }

    if limited_data["annual_reports"]:
        await db.cash_flow.update_one(
            {"ticker": ticker}, {"$set": limited_data}, upsert=True
        )
        logger.info(f"Stored cash flow for {ticker} in database")

    # Cache the result
    cash_flow_cache[cache_key] = limited_data

    return limited_data


# Fetch Earnings
async def fetch_earnings(ticker: str, limit: int = 1):
    cache_key = f"{ticker}_{limit}"
    if cache_key in earnings_cache:
        return earnings_cache[cache_key]

    # Check if earnings are already stored in the database
    db = await database.get_db()
    existing_earnings = await db.earnings.find_one({"ticker": ticker})
    if existing_earnings:
        existing_earnings["_id"] = str(existing_earnings["_id"])
        return existing_earnings

    data = await make_fmp_request("/earnings", {"symbol": ticker, "limit": limit})
    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="FMP returned no earnings data.")

    # Process the data to limit the number of earnings
    limited_data = {
        "ticker": ticker,
        "annual_reports": data[:limit],
    }

    if limited_data["annual_reports"]:
        await db.earnings.update_one(
            {"ticker": ticker}, {"$set": limited_data}, upsert=True
        )
        logger.info(f"Stored earnings for {ticker} in database")

    # Cache the result
    earnings_cache[cache_key] = limited_data

    return limited_data


async def fetch_financial_metrics(ticker: str, limit: int = 1):
    """Fetch FMP key metrics and ratios for supplemental analysis."""
    key_metrics = await make_fmp_request(
        "/key-metrics", {"symbol": ticker, "limit": limit}
    )
    ratios = await make_fmp_request("/ratios", {"symbol": ticker, "limit": limit})
    return {
        "key_metrics": key_metrics if isinstance(key_metrics, list) else [],
        "ratios": ratios if isinstance(ratios, list) else [],
    }


# Fetch SMA
async def fetch_SMA(
    ticker: str,
    interval: str = "weekly",
    time_period: int = 60,
    series_type: str = "close",
    limit: int = 12,
):
    """
    SMA (Simple Moving Average) is represented by a line on a stock chart that follows that previous n days closing price
        - When a stock goes below the line, it represents a bearish market (downward trend)
        - When a stock goes above the line, it represents a bullish market (upward trend)
        Trading Technique:
            - Buy when a goes above line
            - Sell when it goes below the line
    """
    cache_key = f"{ticker}_{limit}"
    if cache_key in sma_cache:
        return sma_cache[cache_key]

    data = await make_fmp_request(
        "/historical-price-eod/full",
        {"symbol": ticker, "limit": time_period + limit - 1},
    )
    prices = (
        [
            (item.get("date"), item.get("close"))
            for item in data
            if item.get("date") and item.get("close") is not None
        ]
        if isinstance(data, list)
        else []
    )
    limited_sma_data = {}
    for index in range(len(prices) - time_period + 1):
        window = [value for _, value in prices[index : index + time_period]]
        limited_sma_data[prices[index][0]] = {"SMA": sum(window) / len(window)}
        if len(limited_sma_data) == limit:
            break

    # Cache the result
    sma_cache[cache_key] = limited_sma_data

    return limited_sma_data


# Fetch EMA
async def fetch_EMA(
    ticker: str,
    interval: str = "weekly",
    time_period: int = 60,
    series_type: str = "close",
    limit: int = 12,
):
    """
    EMA (Exponential Moving Average) is represented by a line on a stock chart that follows that previous n days closing price
        The difference here compared to SMA is that the EMA places a bigger weight on more recent days,
            and less weight on days further away
        - When a stock goes below the line, it represents a bearish market (downward trend)
        - When a stock goes above the line, it represents a bullish market (upward trend)
        Trading Technique:
            - Buy when a goes above line
            - Sell when it goes below the line
    """
    cache_key = f"{ticker}_{limit}"
    if cache_key in ema_cache:
        return ema_cache[cache_key]

    data = await make_fmp_request(
        "/historical-price-eod/full",
        {"symbol": ticker, "limit": time_period + limit - 1},
    )
    prices = (
        [
            (item.get("date"), item.get("close"))
            for item in data
            if item.get("date") and item.get("close") is not None
        ]
        if isinstance(data, list)
        else []
    )
    limited_ema_data: dict[str, dict[str, float]] = {}
    if len(prices) >= time_period:
        multiplier = 2 / (time_period + 1)
        ema_value = sum(value for _, value in prices[-time_period:]) / time_period
        for date, price in reversed(prices[:-time_period]):
            ema_value = (price - ema_value) * multiplier + ema_value
            if len(limited_ema_data) < limit:
                limited_ema_data[date] = {"EMA": ema_value}

    # Cache the result
    ema_cache[cache_key] = limited_ema_data

    return limited_ema_data


"""
Fetching live market data -----------------------
"""


async def fetch_live_market_prices():
    """
    Fetching live market prices for specified stocks to display in the frontend
    """
    global market_data_cache  # noqa: F824
    current_time = time.time()

    # Refresh market data every 60 minutes
    if current_time - market_data_cache["last_updated"] < 3600:
        print("Returning cached market data")
        return market_data_cache["data"]

    symbols = ["AAPL", "AMZN", "TSLA", "MSFT", "GOOG", "NVDA"]
    interval = "daily"

    market_data = {}

    for symbol in symbols:
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
            data = await make_request(url)

            # Check if API returned an error
            if "Error Message" in data or not data:
                print(
                    f"API Error for {symbol}: {data.get('Error Message', 'Unknown error')}"
                )
                market_data[symbol] = {"current_price": None, "price_5_days_ago": None}
                continue

            # Verify correct data structure
            time_series = data.get("Time Series (Daily)", {})

            if not time_series:
                print(f"Warning: No time series data found for {symbol}")
                market_data[symbol] = {"current_price": None, "price_5_days_ago": None}
                continue

            # Get the latest timestamp
            sorted_dates = sorted(time_series.keys(), reverse=True)
            latest_time = sorted_dates[0] if sorted_dates else None
            time_5_days_ago = sorted_dates[5] if len(sorted_dates) > 5 else None

            if not latest_time or not time_5_days_ago:
                print(f"Warning: No valid timestamp for {symbol}")
                market_data[symbol] = {"current_price": None, "price_5_days_ago": None}
                continue

            latest_data = time_series[latest_time]
            data_5_days_ago = time_series[time_5_days_ago]

            # Extract closing prices
            current_price = float(latest_data["4. close"])
            price_5_days_ago = float(data_5_days_ago["4. close"])

            market_data[symbol] = {
                "current_price": current_price,
                "price_5_days_ago": price_5_days_ago,
            }

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            market_data[symbol] = {"current_price": None, "price_5_days_ago": None}

    # Update cache
    market_data_cache["data"] = market_data
    market_data_cache["last_updated"] = current_time

    return market_data


async def fetch_top_gainers_losers(limit: int = 5):
    """
    Fetch the top gainers and losers from the FMP API.
    If the API fails or returns no data, return mock data.
    """
    cache_key = f"top_gainers_losers_{limit}"
    if cache_key in top_gainers_losers_cache:
        return top_gainers_losers_cache[cache_key]

    try:
        # Corrected URL without the 'symbol' parameter
        url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={API_KEY}"
        data = await make_request(url)

        # Check if API returned a valid response
        gainers = data.get("top_gainers", [])[:limit]  # Use an empty list as fallback
        losers = data.get("top_losers", [])[:limit]  # Use an empty list as fallback

        # If gainers or losers are empty, use mock data
        if not gainers:
            gainers = [
                {
                    "ticker": f"MOCK_GAINER_{i+1}",
                    "price": round(100 + i * 10, 2),
                    "change_amount": round(5 + i, 2),
                    "change_percentage": round(2.5 + i * 0.5, 2),
                    "volume": 100000 + i * 1000,
                }
                for i in range(limit)
            ]

        if not losers:
            losers = [
                {
                    "ticker": f"MOCK_LOSER_{i+1}",
                    "price": round(100 - i * 10, 2),
                    "change_amount": round(-5 - i, 2),
                    "change_percentage": round(-2.5 - i * 0.5, 2),
                    "volume": 100000 - i * 1000,
                }
                for i in range(limit)
            ]

        # Format the result
        result = {
            "metadata": data.get("metadata", "No metadata available"),
            "last_updated": data.get("last_updated", "Unknown"),
            "gainers": [
                {
                    "ticker": gainer.get("ticker", "N/A"),
                    "price": gainer.get("price", "N/A"),
                    "change_amount": gainer.get("change_amount", "N/A"),
                    "change_percentage": gainer.get("change_percentage", "N/A"),
                    "volume": gainer.get("volume", "N/A"),
                }
                for gainer in gainers
            ],
            "losers": [
                {
                    "ticker": loser.get("ticker", "N/A"),
                    "price": loser.get("price", "N/A"),
                    "change_amount": loser.get("change_amount", "N/A"),
                    "change_percentage": loser.get("change_percentage", "N/A"),
                    "volume": loser.get("volume", "N/A"),
                }
                for loser in losers
            ],
        }

        # Cache the result
        top_gainers_losers_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"Failed to fetch top gainers and losers: {str(e)}")
        # Return mock data as a fallback
        return {
            "metadata": "Mock metadata",
            "last_updated": "Mock timestamp",
            "gainers": [
                {
                    "ticker": f"MOCK_GAINER_{i+1}",
                    "price": round(100 + i * 10, 2),
                    "change_amount": round(5 + i, 2),
                    "change_percentage": round(2.5 + i * 0.5, 2),
                    "volume": 100000 + i * 1000,
                }
                for i in range(limit)
            ],
            "losers": [
                {
                    "ticker": f"MOCK_LOSER_{i+1}",
                    "price": round(100 - i * 10, 2),
                    "change_amount": round(-5 - i, 2),
                    "change_percentage": round(-2.5 - i * 0.5, 2),
                    "volume": 100000 - i * 1000,
                }
                for i in range(limit)
            ],
        }
