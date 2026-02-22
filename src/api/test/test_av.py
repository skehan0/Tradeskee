import requests
from fastapi import HTTPException
from cachetools import TTLCache
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Load environment variables from .env file
load_dotenv()

# Load Alpha Vantage API key from environment variable
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
# Only raise error if not in testing environment
if not API_KEY and not os.getenv("TESTING", False):
    raise ValueError("Alpha Vantage API key is not set in environment variables.")

# MongoDB setup
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.tradely  # Use the 'tradely' database

# Caches with a TTL of 1 hour and a max size of 100 items
metadata_cache = TTLCache(maxsize=100, ttl=3600)

# Helper function for API requests
async def make_request(url: str):
    """Handles API requests and rate limit errors."""
    response = requests.get(url)
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Alpha Vantage.")
    return response.json()

async def fetch_stock_metadata(ticker: str):
    if ticker in metadata_cache:
        return metadata_cache[ticker]

    # Check if metadata is already stored in the database
    existing_metadata = await db.stock_metadata.find_one({"ticker": ticker})
    if existing_metadata:
        return existing_metadata

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
    }

    # Store in MongoDB
    await db.stock_metadata.insert_one(metadata)

    # Update cache
    metadata_cache[ticker] = metadata

    return metadata

# Example usage
async def main():
    ticker = "TSLA"
    metadata = await fetch_stock_metadata(ticker)
    print(metadata)

if __name__ == "__main__":
    asyncio.run(main())