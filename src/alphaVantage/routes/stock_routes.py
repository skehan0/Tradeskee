from fastapi import APIRouter, HTTPException, Query
from src.alphaVantage.services.stock_services import (
    fetch_stock_metadata,
    fetch_historical_data,
    fetch_news_headlines,
    fetch_live_news_headlines,
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cash_flow,
    fetch_earnings,
    fetch_SMA,
    fetch_EMA,
    fetch_live_market_prices,
    fetch_all_stock_data,
    fetch_top_gainers_losers
)
from src.LLM.LLM_service import fetch_and_analyze_all_stock_data, process_question_with_llm
from src.mongoDB.database import database
from pydantic import BaseModel
from src.alphaVantage.test.mock_live_news import mock_news_data
from src.feature.logging import build_app_logger, StdoutLoggingService

router = APIRouter()
logger = build_app_logger(handlers=[StdoutLoggingService()])

# Request model for the Ask Question endpoint
class QuestionRequest(BaseModel):
    question: str
    context: str = 'You are a stock market enthusiast'  # Optional context (e.g., stock analysis)

# Main Endpoint
@router.get("/analyze_all/{ticker}")
async def analyze_all_stock_data(ticker: str):
    """
    Endpoint to fetch all stock data, analyze it (stage 1), send it to the LLM to analyze (stage 2)
    """
    logger.info("Stock analysis requested", ticker=ticker, endpoint="analyze_all")
    try:
        # Call the service function to fetch, analyze, and send data to the LLM
        result = await fetch_and_analyze_all_stock_data(ticker)
        logger.info("Stock analysis completed", ticker=ticker)
        # Return the result
        return result
    except ValueError as e:
        logger.error("Stock analysis failed - not found", ticker=ticker, error=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error("Stock analysis failed - runtime error", ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{ticker}")
async def get_stock_metadata(ticker: str):
    logger.debug("Stock metadata requested", ticker=ticker)
    return await fetch_stock_metadata(ticker)

@router.get("/historical/{ticker}")
async def get_historical_data(ticker: str):
    logger.debug("Historical data requested", ticker=ticker)
    return await fetch_historical_data(ticker)

@router.get("/news/{ticker}")
async def get_news_headlines(ticker: str, limit: int = Query(5, description="Number of news items to return")):
    return await fetch_news_headlines(ticker, limit)

@router.get("/live-news-headlines")
async def get_live_news_headlines(limit: int = Query(3, description="Number of news items to return")):
    news = await fetch_live_news_headlines(limit)
    return {"feed": news}

# Mock News Return
# @router.get("/live-news-headlines")
# async def get_live_news_headlines(limit: int = Query(3, description="Number of news items to return")):
#     news = await fetch_live_news_headlines(limit)
#     # return {"feed": news}
#     return mock_news_data["feed"]["news"][:limit]

# Financial Statement
@router.get("/income/{ticker}")
async def get_income_statement(ticker: str, limit: int = Query(5, description="Number of years and quarters to return")):
    return await fetch_income_statement(ticker, limit)

# Financial Statement
@router.get("/balance/{ticker}")
async def get_balance_sheet(ticker: str, limit: int = Query(5, description="Number of years and quarters to return")):
    return await fetch_balance_sheet(ticker)

# Financial Statement
@router.get("/cashflow/{ticker}")
async def get_cash_flow(ticker: str, limit: int = Query(5, description="Number of years and quarters to return")):
    return await fetch_cash_flow(ticker, limit)

# Financial Statement
@router.get("/earnings/{ticker}")
async def get_earnings(ticker: str, limit: int = Query(5, description="Number of years and quarters to return")):
    return await fetch_earnings(ticker, limit)

@router.get("/live-market-prices")
async def get_live_market_prices():
    logger.info("Live market prices requested")
    try:
        data = await fetch_live_market_prices()
        logger.debug("Live market prices fetched successfully")
        return data
    except Exception as e:
        logger.error("Failed to fetch live market prices", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Financial Indicator
@router.get("/sma/{ticker}")
async def get_SMA(ticker: str):
    return await fetch_SMA(ticker)

# Financial Indicator
@router.get("/ema/{ticker}")
async def get_EMA(ticker: str):
    return await fetch_EMA(ticker)

@router.get("/all-stock-data/{ticker}")
async def get_all_stock_data(ticker: str):
    return await fetch_all_stock_data(ticker)

@router.get("/top-gainers-losers")
async def get_top_gainers_losers(limit: int = Query(5, description="Number of gainers and losers to return")):
    return await fetch_top_gainers_losers(limit)

@router.post("/ask-question")
async def post_process_question_with_llm(request: QuestionRequest):
    try:
        # Call the LLM service
        llm_response = await process_question_with_llm(request.question, request.context)

        return {"answer": llm_response}  # Wrap the response in a JSON object
    except Exception as e:
        print(f"Error in post_process_question_with_llm: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.get("/status")
async def check_db_status():
    try:
        db = await database.get_db()
        collections = await db.list_collection_names()
        return {"status": "Connected successfully!", "collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")