# from src.alphaVantage.services.stock_services import make_request, income_statement_cache, balance_sheet_cache, cash_flow_cache
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

# # Fetch Income Statement
# async def fetch_income_statement(ticker: str, limit: int = 1):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in income_statement_cache:
#         return income_statement_cache[cache_key]
    
#     # Check if income statement is already stored in the database
#     existing_income_statement = await db.income_statement.find_one({"ticker": ticker})
#     if existing_income_statement:
#         existing_income_statement["_id"] = str(existing_income_statement["_id"])
#         return existing_income_statement
    
#     url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={API_KEY}"
#     data = await make_request(url)

#     # Process the data to limit the number of statements
#     limited_data = {
#         "ticker": ticker,
#         "annual_reports": data.get("annualReports", [])[:limit],
#         # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
#     }

#     # Store in MongoDB
#     await db.income_statement.update_one(
#         {"ticker": ticker},
#         {"$set": limited_data},
#         upsert=True
#     )
#     logger.info(f"Stored income statement for {ticker} in database")

#     # Cache the result
#     income_statement_cache[cache_key] = limited_data

#     return limited_data

# # Fetch Balance Sheet
# async def fetch_balance_sheet(ticker: str, limit: int = 1):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in balance_sheet_cache:
#         return balance_sheet_cache[cache_key]
    
#     # Check if balance sheet is already stored in the database
#     existing_balance_sheet = await db.balance_sheet.find_one({"ticker": ticker})
#     if existing_balance_sheet:
#         existing_balance_sheet["_id"] = str(existing_balance_sheet["_id"])
#         return existing_balance_sheet
    
#     url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={API_KEY}"
#     data = await make_request(url)

#     # Process the data to limit the number of balance sheets
#     limited_data = {
#         "ticker": ticker,
#         "annual_reports": data.get("annualReports", [])[:limit],
#         # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
#     }

#     # Store in MongoDB
#     await db.balance_sheet.update_one(
#         {"ticker": ticker},
#         {"$set": limited_data},
#         upsert=True
#     )
#     logger.info(f"Stored balance sheet for {ticker} in database")

#     # Cache the result
#     balance_sheet_cache[cache_key] = limited_data

#     return limited_data

# # Fetch Cash Flow
# async def fetch_cash_flow(ticker: str, limit: int = 1):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in cash_flow_cache:
#         return cash_flow_cache[cache_key]
    
#     url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={API_KEY}"
#     data = await make_request(url)
    
#     # Check if cash flow is already stored in the database
#     existing_cash_flow = await db.cash_flow.find_one({"ticker": ticker})
#     if existing_cash_flow:
#         existing_cash_flow["_id"] = str(existing_cash_flow["_id"])
#         return existing_cash_flow
    
#     # Process the data to limit the number of cash flows
#     limited_data = {
#         "ticker": ticker,
#         "annual_reports": data.get("annualReports", [])[:limit],
#         # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
#     }

#     # Store in MongoDB
#     await db.cash_flow.update_one(
#         {"ticker": ticker},
#         {"$set": limited_data},
#         upsert=True
#     )
#     logger.info(f"Stored cash flow for {ticker} in database")

#     # Cache the result
#     cash_flow_cache[cache_key] = limited_data

#     return limited_data

# # Fetch Earnings
# async def fetch_earnings(ticker: str, limit: int = 1):
#     cache_key = f"{ticker}_{limit}"
#     if cache_key in earnings_cache:
#         return earnings_cache[cache_key]
    
#     # Check if earnings are already stored in the database
#     existing_earnings = await db.earnings.find_one({"ticker": ticker})
#     if existing_earnings:
#         existing_earnings["_id"] = str(existing_earnings["_id"])
#         return existing_earnings
    
#     url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={API_KEY}"
#     data = await make_request(url)
    
#     # Process the data to limit the number of earnings
#     limited_data = {
#         "ticker": ticker,
#         "annual_reports": data.get("annualReports", [])[:limit],
#         # "quarterly_reports": data.get("quarterlyReports", [])[:limit]
#     }
    
#     # Store in MongoDB
#     await db.earnings.update_one(
#         {"ticker": ticker},
#         {"$set": limited_data},
#         upsert=True
#     )
#     logger.info(f"Stored earnings for {ticker} in database")

#     # Cache the result
#     earnings_cache[cache_key] = limited_data

#     return limited_data