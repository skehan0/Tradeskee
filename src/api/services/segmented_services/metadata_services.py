# from src.alphaVantage.services.stock_services import make_request, metadata_cache
# from fastapi import HTTPException
# from cachetools import TTLCache
# from datetime import datetime
# from src.mongoDB.database import database
# import logging
# from dotenv import load_dotenv
# import os
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

# # Specific Data Calls
# async def fetch_stock_metadata(ticker: str):
#     if ticker in metadata_cache:
#         return metadata_cache[ticker]
    
#     url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={API_KEY}"
#     data = await make_request(url)

#     metadata = {
#         "ticker": ticker,
#         "industry": data.get("Industry", "N/A"),
#         "market_cap": data.get("MarketCapitalization", "N/A"),
#         "dividend_yield": data.get("DividendYield", "N/A"),
#         "pe_ratio": data.get("PERatio", "N/A"),
#         "eps": data.get("EPS", "N/A"),
#         "beta": data.get("Beta", "N/A"),
#         "52_week_high": data.get("52WeekHigh", "N/A"),
#         "52_week_low": data.get("52WeekLow", "N/A"),
#         "current_price": data.get("50DayMovingAverage", "N/A"),
#         "analyst_ratings": data.get("AnalystTargetPrice", "N/A"),
#         "price_targets": data.get("AnalystTargetPrice", "N/A"),
#         "events": data.get("QuarterlyEarningsGrowthYOY", "N/A"),
#         f"about_{ticker}": data.get("Description", "N/A"),
#         "last_updated": datetime.utcnow()
#     }

#     # Store in MongoDB (overwrite existing data)
#     await db.stock_metadata.update_one(
#         {"ticker": ticker},
#         {"$set": metadata},
#         upsert=True
#     )
#     logger.info(f"Stored metadata for {ticker} in database")

#     # Update cache
#     metadata_cache[ticker] = metadata

#     return metadata