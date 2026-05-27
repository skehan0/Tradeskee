# from src.alphaVantage.services.stock_services import make_request, news_cache
# from fastapi import HTTPException
# from cachetools import TTLCache
# import os
# from dotenv import load_dotenv
# import logging
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

# async def fetch_news_headlines(ticker: str, limit: int = 3):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in news_cache:
#         return news_cache[cache_key]

#     url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&apikey={API_KEY}&sort=RELEVANCE"
#     data = await make_request(url)
#     news_data = data.get("feed", [])

#     cleaned_news = [
#         {
#             "article": index + 1,
#             "title": item.get("title", "N/A"),
#             "summary": item.get("summary", "N/A"),
#             "pubDate": item.get("time_published", "N/A"),
#             "url": item.get("url", "N/A"),
#             "thumbnail": item.get("banner_image", "N/A"),
#             "sentimentScore": item.get("overall_sentiment_score", "N/A"),
#             "sentimentLabel": item.get("overall_sentiment_label", "N/A"),
#         }
#         for index, item in enumerate(news_data[:limit])
#     ]

#     result = {"company": ticker, "news": cleaned_news}
#     news_cache[cache_key] = result
#     return result