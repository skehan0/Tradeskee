import requests
from fastapi import HTTPException
import asyncio

async def make_request(url: str, retries: int = 3, backoff_factor: float = 0.5):
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