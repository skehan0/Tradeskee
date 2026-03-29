# from src.alphaVantage.services.stock_services import make_request, historical_data_cache
# from fastapi import HTTPException
# from cachetools import TTLCache
# import os
# from datetime import datetime
# from alpha_vantage.timeseries import TimeSeries
# from src.mongoDB.database import database
# import logging
# from dotenv import load_dotenv
# from motor.motor_asyncio import AsyncIOMotorClient

# # Load environment variables from .env file
# load_dotenv()

# # Load Alpha Vantage API key from environment variable
# API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
# if not API_KEY:
#     raise ValueError("Alpha Vantage API key is not set in environment variables.")

# # MongoDB setup
# client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
# db = client.tradely

# async def fetch_historical_data(ticker: str, limit: int = 5):
#     """
#     Fetch weekly historical stock data with a limit on the number of entries.
#     """
#     if ticker in historical_data_cache:
#         # Return limited data from the cache
#         cached_data = historical_data_cache[ticker]
#         cached_data["historical_data"] = cached_data["historical_data"][:limit]
#         return cached_data

#     # Check if historical data is already stored in the database
#     existing_data = await db.historical_data.find_one({"ticker": ticker})
#     if existing_data:
#         existing_data["_id"] = str(existing_data["_id"])
#         # Limit the number of entries
#         existing_data["historical_data"] = existing_data["historical_data"][:limit]
#         return existing_data

#     try:
#         ts = TimeSeries(key=os.getenv("ALPHA_VANTAGE_API_KEY"), output_format='json')
#         data, _ = ts.get_weekly_adjusted(ticker)

#         # Extract relevant details and limit the number of entries
#         cleaned_data = [
#             {
#                 "date": date,
#                 "open": values["1. open"],
#                 "high": values["2. high"],
#                 "low": values["3. low"],
#                 "close": values["4. close"],
#                 "adjusted_close": values["5. adjusted close"],
#                 "volume": values["6. volume"],
#                 "dividend_amount": values["7. dividend amount"]
#             }
#             for date, values in data.items()
#         ][:limit]  # Apply the limit here

#         historical_data = {
#             "ticker": ticker,
#             "historical_data": cleaned_data,
#             "last_updated": datetime.utcnow()
#         }

#         # Store in MongoDB
#         await db.historical_data.update_one(
#             {"ticker": ticker},
#             {"$set": historical_data},
#             upsert=True
#         )
#         logger.info(f"Stored historical data for {ticker} in database")

#         # Update cache
#         historical_data_cache[ticker] = historical_data

#         return historical_data

#     except Exception as e:
#         logger.error(f"Failed to fetch historical data for {ticker}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

# async def fetch_SMA(ticker: str, interval: str = "weekly", time_period: int = 60, series_type: str = "close", limit: int = 12):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in sma_cache:
#         return sma_cache[cache_key]
    
#     url = f"https://www.alphavantage.co/query?function=SMA&symbol={ticker}&interval={interval}&time_period={time_period}&series_type={series_type}&apikey={API_KEY}"
#     data = await make_request(url)
#     sma_data = data.get("Technical Analysis: SMA", {})
    
#     # Limit the data to the last 'limit' entries
#     limited_sma_data = dict(list(sma_data.items())[:limit])
    
#     # Cache the result
#     sma_cache[cache_key] = limited_sma_data

#     return limited_sma_data

# async def fetch_EMA(ticker: str, interval: str = "weekly", time_period: int = 60, series_type: str = "close", limit: int = 12):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in ema_cache:
#         return ema_cache[cache_key]
    
#     url = f"https://www.alphavantage.co/query?function=EMA&symbol={ticker}&interval={interval}&time_period={time_period}&series_type={series_type}&apikey={API_KEY}"
#     data = await make_request(url)
#     ema_data = data.get("Technical Analysis: EMA", {})
    
#     # Limit the data to the last 'limit' entries
#     limited_ema_data = dict(list(ema_data.items())[:limit])
    
#     # Cache the result
#     ema_cache[cache_key] = limited_ema_data

#     return limited_ema_data