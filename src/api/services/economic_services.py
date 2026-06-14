import os

import requests
from cachetools import TTLCache
from dotenv import load_dotenv
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from src.infrastructure.database.mongoDB.database import database

# Load environment variables from .env file
load_dotenv()

# Load Alpha Vantage API key from environment variable
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
# Only raise error if not in testing environment
if not API_KEY and not os.getenv("TESTING", False):
    raise ValueError("Alpha Vantage API key is not set in environment variables.")

# MongoDB setup
client: AsyncIOMotorClient = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.tradely  # Use the 'tradely' database

# Caches with a TTL of 1 hour and a max size of 100 items
economic_cache = TTLCache(maxsize=100, ttl=3600)


# Helper function for API requests
async def make_request(url: str):
    """Handles API requests and rate limit errors."""
    response = requests.get(url)
    if response.status_code == 429:
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch data from Alpha Vantage.",
        )
    return response.json()


async def fetch_economic_data(indicator: str):
    if indicator in economic_cache:
        return economic_cache[indicator]

    url = f"https://www.alphavantage.co/query?function={indicator}&apikey={API_KEY}"
    data = await make_request(url)

    # Store in MongoDB
    result = await db.economic_data.insert_one(data)
    data["_id"] = str(result.inserted_id)

    # Update cache
    economic_cache[indicator] = data

    return data
