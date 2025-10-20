import requests
from fastapi import HTTPException
from cachetools import TTLCache
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from alpha_vantage.timeseries import TimeSeries
from src.alphaVantage.models.stock_models import StockMetadata, StockHistoricalData
from src.mongoDB.database import database
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import logging
import time

# Load environment variables from .env file
load_dotenv()

# Load Alpha Vantage API key from environment variable
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
# Only raise error if not in testing environment
if not API_KEY and not os.getenv("TESTING", False):
    raise ValueError("Alpha Vantage API key is not set in environment variables.")

# MongoDB setup
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.tradely

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
    Handles API requests and rate limit errors with retries
        429 == rate limit exceeded
        200 == success
        Not 429 || 200 == HTTPException
        500 == retry attempts fail
    """
    for attempt in range(retries):
        response = requests.get(url)
        if response.status_code == 429:
            if attempt < retries - 1:
                await asyncio.sleep(backoff_factor * (2 ** attempt))
                continue
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Alpha Vantage.")
        return response.json()
    raise HTTPException(status_code=500, detail="Failed to fetch data after multiple attempts.")

async def fetch_all_stock_data(ticker: str):
    """
    Fetch all relevant stock data by calling multiple endpoints.
    """
    try:
        # Step 1: Fetch metadata
        metadata = await fetch_stock_metadata(ticker)

        # Step 2: Fetch historical data
        historical_data = await fetch_historical_data(ticker)
        
        # Step 3: Fetch news headlines
        news = await fetch_news_headlines(ticker)
        
        # Step 4: Fetch income statement
        income_statement = await fetch_income_statement(ticker)
        
        # Step 5: Fetch balance sheet
        balance_sheet = await fetch_balance_sheet(ticker)

        # Step 6: Fetch cash flow
        cash_flow = await fetch_cash_flow(ticker)

        # Step 7: Fetch earnings
        earnings = await fetch_earnings(ticker)

        # Step 8: Fetch SMA (Simple Moving Average)
        sma = await fetch_SMA(ticker)

        # Step 9: Fetch EMA (Exponential Moving Average)
        ema = await fetch_EMA(ticker)

        # Step 10: Fetch live market prices
        live_market_prices = await fetch_live_market_prices()

        # Step 11: Consolidate all data into a single dictionary
        consolidated_data = {
            "metadata": metadata,
            "historical_data": historical_data,
            "news": news,
            "income_statement": income_statement,
            "balance_sheet": balance_sheet,
            "cash_flow": cash_flow,
            "earnings": earnings,
            "sma": sma,
            "ema": ema,
        }

        return consolidated_data

    except Exception as e:
        logger.error(f"Failed to fetch all stock data for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch all stock data: {str(e)}")


# Specific Data Calls
async def fetch_stock_metadata(ticker: str):
    """
    Fetching stock metadata of a specific ticker input symbol
    """
    if ticker in metadata_cache:
        return metadata_cache[ticker]
    
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={API_KEY}"
    data = await make_request(url)

    metadata = {
        "ticker": ticker,
        "industry": data.get("Industry", "N/A"),
        "market_cap": data.get("MarketCapitalization", "N/A"),
        "dividend_yield": data.get("DividendYield", "N/A"),
        "pe_ratio": data.get("PERatio", "N/A"),
        "eps": data.get("EPS", "N/A"),
        "beta": data.get("Beta", "N/A"),
        "52_week_high": data.get("52WeekHigh", "N/A"),
        "52_week_low": data.get("52WeekLow", "N/A"),
        "current_price": data.get("50DayMovingAverage", "N/A"),
        "analyst_ratings": data.get("AnalystTargetPrice", "N/A"),
        "price_targets": data.get("AnalystTargetPrice", "N/A"),
        "events": data.get("QuarterlyEarningsGrowthYOY", "N/A"),
        f"about_{ticker}": data.get("Description", "N/A"),
        "last_updated": datetime.utcnow()
    }

    # Store in MongoDB (overwrite existing data)
    await db.stock_metadata.update_one(
        {"ticker": ticker},
        {"$set": metadata},
        upsert=True
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
        cached_data = historical_data_cache[ticker]
        cached_data["historical_data"] = cached_data["historical_data"][:limit]
        return cached_data

    # Check if historical data is already stored in the database
    existing_data = await db.historical_data.find_one({"ticker": ticker})
    if existing_data:
        existing_data["_id"] = str(existing_data["_id"])
        # Limit the number of entries
        existing_data["historical_data"] = existing_data["historical_data"][:limit]
        return existing_data

    try:
        ts = TimeSeries(key=os.getenv("ALPHA_VANTAGE_API_KEY"), output_format='json')
        data, _ = ts.get_weekly_adjusted(ticker)

        # Extract relevant details and limit the number of entries
        cleaned_data = [
            {
                "date": date,
                "open": values["1. open"],
                "high": values["2. high"],
                "low": values["3. low"],
                "close": values["4. close"],
                "adjusted_close": values["5. adjusted close"],
                "volume": values["6. volume"],
                "dividend_amount": values["7. dividend amount"]
            }
            for date, values in data.items()
        ][:limit]  # Apply the limit here

        historical_data = {
            "ticker": ticker,
            "historical_data": cleaned_data,
            "last_updated": datetime.utcnow()
        }

        # Store in MongoDB
        await db.historical_data.update_one(
            {"ticker": ticker},
            {"$set": historical_data},
            upsert=True
        )
        logger.info(f"Stored historical data for {ticker} in database")

        # Update cache
        historical_data_cache[ticker] = historical_data

        return historical_data

    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

# Fetch news headlines
async def fetch_news_headlines(ticker: str, limit: int = 3):
    """
    Stock news for specific ticker input
    """
    cache_key = f"{ticker}_{limit}"
    if cache_key in news_cache:
        return news_cache[cache_key]

    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={API_KEY}&sort=RELEVANCE"

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
    existing_income_statement = await db.income_statement.find_one({"ticker": ticker})
    if existing_income_statement:
        existing_income_statement["_id"] = str(existing_income_statement["_id"])
        return existing_income_statement
    
    url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={API_KEY}"
    data = await make_request(url)

    # Process the data to limit the number of statements
    limited_data = {
        "ticker": ticker,
        "annual_reports": data.get("annualReports", [])[:limit],
        # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
    }

    # Store in MongoDB
    await db.income_statement.update_one(
        {"ticker": ticker},
        {"$set": limited_data},
        upsert=True
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
    existing_balance_sheet = await db.balance_sheet.find_one({"ticker": ticker})
    if existing_balance_sheet:
        existing_balance_sheet["_id"] = str(existing_balance_sheet["_id"])
        return existing_balance_sheet
    
    url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={API_KEY}"
    data = await make_request(url)

    # Process the data to limit the number of balance sheets
    limited_data = {
        "ticker": ticker,
        "annual_reports": data.get("annualReports", [])[:limit],
        # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
    }

    # Store in MongoDB
    await db.balance_sheet.update_one(
        {"ticker": ticker},
        {"$set": limited_data},
        upsert=True
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
    
    url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={API_KEY}"
    data = await make_request(url)
    
    # Check if cash flow is already stored in the database
    existing_cash_flow = await db.cash_flow.find_one({"ticker": ticker})
    if existing_cash_flow:
        existing_cash_flow["_id"] = str(existing_cash_flow["_id"])
        return existing_cash_flow
    
    # Process the data to limit the number of cash flows
    limited_data = {
        "ticker": ticker,
        "annual_reports": data.get("annualReports", [])[:limit],
        # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
    }

    # Store in MongoDB
    await db.cash_flow.update_one(
        {"ticker": ticker},
        {"$set": limited_data},
        upsert=True
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
    existing_earnings = await db.earnings.find_one({"ticker": ticker})
    if existing_earnings:
        existing_earnings["_id"] = str(existing_earnings["_id"])
        return existing_earnings
    
    url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={API_KEY}"
    data = await make_request(url)
    
    # Process the data to limit the number of earnings
    limited_data = {
        "ticker": ticker,
        "annual_reports": data.get("annualReports", [])[:limit],
        # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
    }
    
    # Store in MongoDB
    await db.earnings.update_one(
        {"ticker": ticker},
        {"$set": limited_data},
        upsert=True
    )
    logger.info(f"Stored earnings for {ticker} in database")

    # Cache the result
    earnings_cache[cache_key] = limited_data

    return limited_data

# Fetch SMA
async def fetch_SMA(ticker: str, interval: str = "weekly", time_period: int = 60, series_type: str = "close", limit: int = 12):
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
    
    url = f"https://www.alphavantage.co/query?function=SMA&symbol={ticker}&interval={interval}&time_period={time_period}&series_type={series_type}&apikey={API_KEY}"
    data = await make_request(url)
    sma_data = data.get("Technical Analysis: SMA", {})
    
    # Limit the data to the last 'limit' entries
    limited_sma_data = dict(list(sma_data.items())[:limit])
    
    # Cache the result
    sma_cache[cache_key] = limited_sma_data

    return limited_sma_data

# Fetch EMA
async def fetch_EMA(ticker: str, interval: str = "weekly", time_period: int = 60, series_type: str = "close", limit: int = 12):
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
    
    url = f"https://www.alphavantage.co/query?function=EMA&symbol={ticker}&interval={interval}&time_period={time_period}&series_type={series_type}&apikey={API_KEY}"
    data = await make_request(url)
    ema_data = data.get("Technical Analysis: EMA", {})
    
    # Limit the data to the last 'limit' entries
    limited_ema_data = dict(list(ema_data.items())[:limit])
    
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
    global market_data_cache
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
                print(f"API Error for {symbol}: {data.get('Error Message', 'Unknown error')}")
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
                "price_5_days_ago": price_5_days_ago
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
    Fetch the top gainers and losers from the Alpha Vantage API.
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
        losers = data.get("top_losers", [])[:limit]    # Use an empty list as fallback

        # If gainers or losers are empty, use mock data
        if not gainers:
            gainers = [
                {
                    "ticker": f"MOCK_GAINER_{i+1}",
                    "price": round(100 + i * 10, 2),
                    "change_amount": round(5 + i, 2),
                    "change_percentage": round(2.5 + i * 0.5, 2),
                    "volume": 100000 + i * 1000
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
                    "volume": 100000 - i * 1000
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
                    "volume": gainer.get("volume", "N/A")
                }
                for gainer in gainers
            ],
            "losers": [
                {
                    "ticker": loser.get("ticker", "N/A"),
                    "price": loser.get("price", "N/A"),
                    "change_amount": loser.get("change_amount", "N/A"),
                    "change_percentage": loser.get("change_percentage", "N/A"),
                    "volume": loser.get("volume", "N/A")
                }
                for loser in losers
            ]
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
                    "volume": 100000 + i * 1000
                }
                for i in range(limit)
            ],
            "losers": [
                {
                    "ticker": f"MOCK_LOSER_{i+1}",
                    "price": round(100 - i * 10, 2),
                    "change_amount": round(-5 - i, 2),
                    "change_percentage": round(-2.5 - i * 0.5, 2),
                    "volume": 100000 - i * 1000
                }
                for i in range(limit)
            ]
        }