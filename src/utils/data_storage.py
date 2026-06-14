from typing import Optional

from src.infrastructure.database.mongoDB.database import database


async def check_if_data_exists(
    collection_name: str, ticker: str, date: Optional[str] = None
):
    collection = await database.get_collection(collection_name)
    if date:
        # If you need to check by date (for historical data), include it in the query
        existing_record = await collection.find_one({"ticker": ticker, "Date": date})
    else:
        # Otherwise, just check by ticker
        existing_record = await collection.find_one({"ticker": ticker})
    return existing_record is not None


async def store_data(collection_name: str, data: dict, ticker: Optional[str] = None):
    collection = await database.get_collection(collection_name)
    if ticker:
        data["ticker"] = ticker
    await collection.insert_one(data)
