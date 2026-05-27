# from src.alphaVantage.services.stock_services import make_request, market_data_cache, top_gainers_losers_cache
# import os
# from dotenv import load_dotenv
# import time
# from motor.motor_asyncio import AsyncIOMotorClient
# import logging

# # Load environment variables from .env file
# load_dotenv()

# # Load Alpha Vantage API key from environment variable
# API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
# if not API_KEY:
#     raise ValueError("Alpha Vantage API key is not set in environment variables.")

# # MongoDB setup
# client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
# db = client.tradely

# # Fetching live market data
# async def fetch_live_market_prices():
#     global market_data_cache
#     current_time = time.time()
    
#     # Refresh market data every 60 minutes
#     if current_time - market_data_cache["last_updated"] < 3600:
#         print("Returning cached market data")
#         return market_data_cache["data"]
    
#     symbols = ["AAPL", "AMZN", "TSLA", "MSFT", "GOOG", "NVDA"]
#     interval = "daily"
    
#     market_data = {}

#     for symbol in symbols:
#         try:
#             url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"
#             data = await make_request(url)
            
#             # Check if API returned an error
#             if "Error Message" in data or not data:
#                 print(f"API Error for {symbol}: {data.get('Error Message', 'Unknown error')}")
#                 market_data[symbol] = {"current_price": None, "price_5_days_ago": None}
#                 continue

#             # Verify correct data structure
#             time_series = data.get("Time Series (Daily)", {})

#             if not time_series:
#                 print(f"Warning: No time series data found for {symbol}")
#                 market_data[symbol] = {"current_price": None, "price_5_days_ago": None}
#                 continue

#             # Get the latest timestamp
#             sorted_dates = sorted(time_series.keys(), reverse=True)
#             latest_time = sorted_dates[0] if sorted_dates else None
#             time_5_days_ago = sorted_dates[5] if len(sorted_dates) > 5 else None

#             if not latest_time or not time_5_days_ago:
#                 print(f"Warning: No valid timestamp for {symbol}")
#                 market_data[symbol] = {"current_price": None, "price_5_days_ago": None}
#                 continue

#             latest_data = time_series[latest_time]
#             data_5_days_ago = time_series[time_5_days_ago]

#             # Extract closing prices
#             current_price = float(latest_data["4. close"])
#             price_5_days_ago = float(data_5_days_ago["4. close"])

#             market_data[symbol] = {
#                 "current_price": current_price,
#                 "price_5_days_ago": price_5_days_ago
#             }

#         except Exception as e:
#             print(f"Error fetching data for {symbol}: {e}")
#             market_data[symbol] = {"current_price": None, "price_5_days_ago": None}

#     # Update cache
#     market_data_cache["data"] = market_data
#     market_data_cache["last_updated"] = current_time

#     return market_data

# # Top gainers and losers
# async def fetch_top_gainers_losers(limit: int = 5):
#     """
#     Fetch the top gainers and losers from the Alpha Vantage API.
#     If the API fails or returns no data, return mock data.
#     """
#     cache_key = f"top_gainers_losers_{limit}"
#     if cache_key in top_gainers_losers_cache:
#         return top_gainers_losers_cache[cache_key]
    
#     try:
#         # Corrected URL without the 'symbol' parameter
#         url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={API_KEY}"
#         data = await make_request(url)
        
#         # Check if API returned a valid response
#         gainers = data.get("top_gainers", [])[:limit]  # Use an empty list as fallback
#         losers = data.get("top_losers", [])[:limit]    # Use an empty list as fallback

#         # If gainers or losers are empty, use mock data
#         if not gainers:
#             gainers = [
#                 {
#                     "ticker": f"MOCK_GAINER_{i+1}",
#                     "price": round(100 + i * 10, 2),
#                     "change_amount": round(5 + i, 2),
#                     "change_percentage": round(2.5 + i * 0.5, 2),
#                     "volume": 100000 + i * 1000
#                 }
#                 for i in range(limit)
#             ]
        
#         if not losers:
#             losers = [
#                 {
#                     "ticker": f"MOCK_LOSER_{i+1}",
#                     "price": round(100 - i * 10, 2),
#                     "change_amount": round(-5 - i, 2),
#                     "change_percentage": round(-2.5 - i * 0.5, 2),
#                     "volume": 100000 - i * 1000
#                 }
#                 for i in range(limit)
#             ]

#         # Format the result
#         result = {
#             "metadata": data.get("metadata", "No metadata available"),
#             "last_updated": data.get("last_updated", "Unknown"),
#             "gainers": [
#                 {
#                     "ticker": gainer.get("ticker", "N/A"),
#                     "price": gainer.get("price", "N/A"),
#                     "change_amount": gainer.get("change_amount", "N/A"),
#                     "change_percentage": gainer.get("change_percentage", "N/A"),
#                     "volume": gainer.get("volume", "N/A")
#                 }
#                 for gainer in gainers
#             ],
#             "losers": [
#                 {
#                     "ticker": loser.get("ticker", "N/A"),
#                     "price": loser.get("price", "N/A"),
#                     "change_amount": loser.get("change_amount", "N/A"),
#                     "change_percentage": loser.get("change_percentage", "N/A"),
#                     "volume": loser.get("volume", "N/A")
#                 }
#                 for loser in losers
#             ]
#         }

#         # Cache the result
#         top_gainers_losers_cache[cache_key] = result

#         return result

#     except Exception as e:
#         logger.error(f"Failed to fetch top gainers and losers: {str(e)}")
#         # Return mock data as a fallback
#         return {
#             "metadata": "Mock metadata",
#             "last_updated": "Mock timestamp",
#             "gainers": [
#                 {
#                     "ticker": f"MOCK_GAINER_{i+1}",
#                     "price": round(100 + i * 10, 2),
#                     "change_amount": round(5 + i, 2),
#                     "change_percentage": round(2.5 + i * 0.5, 2),
#                     "volume": 100000 + i * 1000
#                 }
#                 for i in range(limit)
#             ],
#             "losers": [
#                 {
#                     "ticker": f"MOCK_LOSER_{i+1}",
#                     "price": round(100 - i * 10, 2),
#                     "change_amount": round(-5 - i, 2),
#                     "change_percentage": round(-2.5 - i * 0.5, 2),
#                     "volume": 100000 - i * 1000
#                 }
#                 for i in range(limit)
#             ]
#         }