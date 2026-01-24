from fastapi import HTTPException
from src.alphaVantage.services.stock_services import fetch_all_stock_data
from pymongo import MongoClient
from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from src.utils.streaming_utils import process_streaming_response
from src.utils.validate_stock_data_utils import validate_stock_data
from src.feature.logging import build_app_logger, StdoutLoggingService

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = build_app_logger(handlers=[StdoutLoggingService()])

# MongoDB setup
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.tradely


# Helper function to safely convert to float
def safe_float(value, default=0):
    try:
        return float(value) if value and value != 'N/A' and str(value).lower() != 'none' else default
    except (ValueError, TypeError):
        return default


def perform_analysis(stock_data: dict) -> str:
    """
    Perform analysis on the stock data and return a formatted prompt.
    """
    
    # Extract key data sections
    metadata = stock_data.get('metadata', {})
    historical = stock_data.get('historical_data', {}).get('historical_data', [])
    news = stock_data.get('news', [])
    income_statement = stock_data.get('income_statement', {}).get('annual_reports', [])
    balance_sheet = stock_data.get('balance_sheet', {}).get('annual_reports', [])
    cash_flow = stock_data.get('cash_flow', {}).get('annual_reports', [])
    sma_data = stock_data.get('sma', {})
    ema_data = stock_data.get('ema', {})
    
    # Get the most recent financial data
    latest_income = income_statement[0] if income_statement else {}
    latest_balance = balance_sheet[0] if balance_sheet else {}
    latest_cashflow = cash_flow[0] if cash_flow else {}
    
    # Get recent price data and extract current price from historical data if metadata is N/A
    recent_prices = historical[:5] if historical else []
    current_price = metadata.get('current_price', 'N/A')
    if current_price == 'N/A' and recent_prices:
        current_price = recent_prices[0].get('close', 'N/A')
    
    # Calculate market cap from shares outstanding and current price if not available
    market_cap = metadata.get('market_cap', 'N/A')
    if market_cap == 'N/A' and current_price != 'N/A' and latest_balance.get('commonStockSharesOutstanding'):
        try:
            shares_outstanding = safe_float(latest_balance.get('commonStockSharesOutstanding', 0))
            market_cap = str(int(safe_float(current_price) * shares_outstanding))
        except:
            market_cap = 'N/A'
    
    # Calculate PE ratio if not available
    pe_ratio = metadata.get('pe_ratio', 'N/A')
    if pe_ratio == 'N/A' and current_price != 'N/A' and latest_income.get('netIncome'):
        try:
            shares_outstanding = safe_float(latest_balance.get('commonStockSharesOutstanding', 0))
            if shares_outstanding > 0:
                eps = safe_float(latest_income.get('netIncome', 0)) / shares_outstanding
                if eps > 0:
                    pe_ratio = f"{safe_float(current_price) / eps:.2f}"
        except:
            pe_ratio = 'N/A'
    
    # Calculate EPS if not available
    eps = metadata.get('eps', 'N/A')
    if eps == 'N/A' and latest_income.get('netIncome'):
        try:
            shares_outstanding = safe_float(latest_balance.get('commonStockSharesOutstanding', 0))
            if shares_outstanding > 0:
                eps = f"{safe_float(latest_income.get('netIncome', 0)) / shares_outstanding:.2f}"
        except:
            eps = 'N/A'
    
    # Calculate dividend yield if not available
    dividend_yield = metadata.get('dividend_yield', 'N/A')
    if dividend_yield == 'N/A' and current_price != 'N/A' and latest_cashflow.get('dividendPayoutCommonStock'):
        try:
            shares_outstanding = safe_float(latest_balance.get('commonStockSharesOutstanding', 0))
            if shares_outstanding > 0:
                annual_dividend_per_share = safe_float(latest_cashflow.get('dividendPayoutCommonStock', 0)) / shares_outstanding
                dividend_yield = f"{(annual_dividend_per_share / safe_float(current_price)) * 100:.2f}%"
        except:
            dividend_yield = 'N/A'
    
    # Extract 52-week high/low from historical data if not available
    week_52_high = metadata.get('52_week_high', 'N/A')
    week_52_low = metadata.get('52_week_low', 'N/A')
    if (week_52_high == 'N/A' or week_52_low == 'N/A') and historical:
        try:
            highs = [safe_float(day.get('high', 0)) for day in historical]
            lows = [safe_float(day.get('low', 0)) for day in historical if safe_float(day.get('low', 0)) > 0]
            if highs and week_52_high == 'N/A':
                week_52_high = f"{max(highs):.2f}"
            if lows and week_52_low == 'N/A':
                week_52_low = f"{min(lows):.2f}"
        except:
            pass
    
    # Get latest technical indicators
    latest_sma = list(sma_data.values())[0].get('SMA', 'N/A') if sma_data else 'N/A'
    latest_ema = list(ema_data.values())[0].get('EMA', 'N/A') if ema_data else 'N/A'
    
    # Calculate simple moving average from historical data if technical indicators are missing
    if latest_sma == 'N/A' and len(recent_prices) >= 5:
        try:
            closes = [safe_float(day.get('close', 0)) for day in recent_prices]
            latest_sma = f"{sum(closes) / len(closes):.2f}"
        except:
            latest_sma = 'N/A'
    
    analysis = f"""
    Goal: Conduct a comprehensive financial analysis of {metadata.get('ticker', 'UNKNOWN').upper()} ({metadata.get('about_' + metadata.get('ticker', '').lower(), 'AstraZeneca PLC')}) based on recent market trends, historical data, and technical indicators.

    COMPANY OVERVIEW:
    - Ticker: {metadata.get('ticker', 'N/A').upper()}
    - Industry: {metadata.get('industry', 'Pharmaceutical') if metadata.get('industry', 'N/A') != 'N/A' else 'Pharmaceutical (AstraZeneca)'}
    - Market Cap: ${safe_float(market_cap)/1e9:.1f}B
    - Current Price: ${current_price}
    - 52-Week Range: ${week_52_low} - ${week_52_high}
    
    PRICE DATA & TECHNICAL ANALYSIS:
    - Current Price: ${current_price}
    - Recent 5-Day Performance: {', '.join([f"${day.get('close', 'N/A')}" for day in recent_prices[:5]])}
    - Price Trend: {'Declining' if len(recent_prices) >= 2 and safe_float(recent_prices[0].get('close', 0)) < safe_float(recent_prices[1].get('close', 0)) else 'Rising' if len(recent_prices) >= 2 else 'Stable'}
    - Trading Volume: {f"Avg {sum([safe_float(day.get('volume', 0)) for day in recent_prices[:5]]) / len(recent_prices) / 1e6:.1f}M shares" if recent_prices else 'N/A'}
    - Simple Moving Average (5-day): ${latest_sma}
    - Exponential Moving Average (EMA): ${latest_ema}
    - Price vs SMA: {'Above' if latest_sma != 'N/A' and safe_float(current_price) > safe_float(latest_sma) else 'Below' if latest_sma != 'N/A' else 'N/A'}
    - Price vs EMA: {'Above' if latest_ema != 'N/A' and safe_float(current_price) > safe_float(latest_ema) else 'Below' if latest_ema != 'N/A' else 'N/A'}
    
    FINANCIAL METRICS (Latest Annual):
    - Total Revenue: ${safe_float(latest_income.get('totalRevenue', 0))/1e9:.1f}B
    - Net Income: ${safe_float(latest_income.get('netIncome', 0))/1e9:.1f}B
    - Operating Cash Flow: ${safe_float(latest_cashflow.get('operatingCashflow', 0))/1e9:.1f}B
    - Total Assets: ${safe_float(latest_balance.get('totalAssets', 0))/1e9:.1f}B
    - Total Debt: ${safe_float(latest_balance.get('shortLongTermDebtTotal', 0))/1e9:.1f}B
    - Dividend Payout: ${safe_float(latest_cashflow.get('dividendPayout', 0))/1e9:.1f}B
    - P/E Ratio: {pe_ratio}
    - EPS: ${eps}
    - Dividend Yield: {dividend_yield if dividend_yield != 'N/A' else f"{safe_float(metadata.get('dividend_yield', 0))*100:.2f}%" if metadata.get('dividend_yield', 'N/A') != 'N/A' else 'N/A'}
    - Beta: {metadata.get('beta', 'N/A')}
    - Profit Margin: {(safe_float(latest_income.get('netIncome', 0)) / safe_float(latest_income.get('totalRevenue', 1)) * 100):.1f}%
    - ROE (Return on Equity): {(safe_float(latest_income.get('netIncome', 0)) / safe_float(latest_balance.get('totalShareholderEquity', 1)) * 100):.1f}%
    
    MARKET SENTIMENT & NEWS:
    """
    
    # Add news sentiment analysis
    if news:
        analysis += f"Recent News Articles: {len(news)} articles analyzed\n"
        for article in news[:3]:  # Top 3 articles
            analysis += f"- {article.get('title', 'N/A')}: {article.get('sentimentLabel', 'N/A')} (Score: {article.get('sentimentScore', 'N/A')})\n"
    else:
        analysis += "No recent news data available\n"
    
    analysis += f"""
    - Analyst Price Target: ${metadata.get('price_targets', 'N/A')}
    - Analyst Ratings: {metadata.get('analyst_ratings', 'N/A')}
    
    RISK FACTORS:
    - Beta (Volatility vs Market): {metadata.get('beta', 'N/A')} ({('Low' if safe_float(metadata.get('beta', 1)) < 0.5 else 'Moderate' if safe_float(metadata.get('beta', 1)) < 1.5 else 'High') if metadata.get('beta', 'N/A') != 'N/A' else 'Unknown'} volatility)
    - Debt-to-Assets Ratio: {(safe_float(latest_balance.get('shortLongTermDebtTotal', 0))/safe_float(latest_balance.get('totalAssets', 1))*100) if safe_float(latest_balance.get('totalAssets', 0)) > 0 else 0:.1f}%
    - Debt-to-Equity Ratio: {(safe_float(latest_balance.get('shortLongTermDebtTotal', 0))/safe_float(latest_balance.get('totalShareholderEquity', 1))*100) if safe_float(latest_balance.get('totalShareholderEquity', 0)) > 0 else 0:.1f}%
    - Current Market Position: {(safe_float(current_price)/safe_float(week_52_high)*100) if safe_float(week_52_high) > 0 else 0:.1f}% of 52-week high
    - Cash Flow Health: {'Strong' if safe_float(latest_cashflow.get('operatingCashflow', 0)) > 0 else 'Weak'} (${safe_float(latest_cashflow.get('operatingCashflow', 0))/1e9:.1f}B operating cash flow)
    
    TECHNICAL INDICATORS ANALYSIS:
    - EMA vs SMA Trend: {'Bullish' if latest_ema != 'N/A' and latest_sma != 'N/A' and safe_float(latest_ema) > safe_float(latest_sma) else 'Bearish' if latest_ema != 'N/A' and latest_sma != 'N/A' else 'Unable to determine'}
    - Price Momentum: {'Positive' if latest_sma != 'N/A' and safe_float(current_price) > safe_float(latest_sma) else 'Negative' if latest_sma != 'N/A' else 'Mixed'}
    - Volume Analysis: {'High activity' if recent_prices and safe_float(recent_prices[0].get('volume', 0)) > 10e6 else 'Moderate activity' if recent_prices else 'N/A'}
    - Price Volatility: {'High' if recent_prices and len(recent_prices) >= 3 and (max([safe_float(d.get('high', 0)) for d in recent_prices[:3]]) - min([safe_float(d.get('low', 0)) for d in recent_prices[:3]])) / safe_float(current_price) > 0.05 else 'Moderate' if recent_prices else 'N/A'}
    
    Return Format:
        - Summary: A brief overview of the stock's current trend and financial health.
        - Key Financial Indicators: Price movements, moving averages (SMA/EMA), financial ratios.
        - Market Sentiment: A summary of recent news and analyst sentiment trends.
        - Risk Factors: Highlight volatility, debt levels, and market position risks.

    Warnings:
        - Do not provide direct financial advice.
        - Ensure the response is fact-based and avoids speculation.
        - Keep the response concise, focusing on actionable insights without exceeding 2000 words.
    """
    
    analysis += "\n\nThis is a preliminary Artificial Intelligence (AI) analysis. Please consult a financial advisor for investment decisions."
    return analysis


async def send_prompt_to_llm(prompt: str, model="gemma3:4b") -> str:
    """
    Send the formatted prompt to the LLM asynchronously and return the response.
    """
    url = os.getenv("LLM_API_URL", "http://localhost:11434/api/chat")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    logger.info("Sending prompt to LLM", model=model, url=url)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=1000.0)

            if response.status_code == 200:
                logger.info("LLM response received successfully", model=model)
                llm_response = ""
                async for content in process_streaming_response(response):
                    # Print each chunk as it arrives
                    print(content, end="", flush=True)
                    llm_response += content
                return llm_response
            else:
                logger.error("LLM request failed", status_code=response.status_code, model=model)
                raise RuntimeError(
                    f"Error {response.status_code}: {response.text}")
    except httpx.RequestError as e:
        logger.error("HTTP request to LLM failed", error=str(e), model=model)
        raise RuntimeError(f"HTTP request failed: {str(e)}")
    except Exception as e:
        logger.error("Failed to send prompt to LLM", error=str(e), model=model)
        raise RuntimeError(f"Failed to send prompt to LLM: {str(e)}")


async def send_to_deepseek(llm_response, stock_data=None, model='deepseek-r1:1.5b'):
    """
    Send the LLM response to the DeepThinking model for final analysis.
    """
    print("Debug: llm_response", llm_response)
    print("Debug: stock_data", stock_data)
    url = "http://localhost:11434/api/chat"
    payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": """
            Goal: Use the stock data to analyze the stock in detail. Focus on providing an in-depth analysis of the stock's performance, trends, risks, and actionable insights.

            Instructions:
            - You are a professional financial analyst with expertise in equity markets, technical indicators, and industry trends.
            - Conduct a deep analysis of the stock using the data provided. 
            - Review the Gemini-generated analysis {llm_response} and incorporate relevant parts if they align with the deeper analysis.
            - Present a structured, professional-level report suitable for senior financial officers, using bullet points where appropriate.
            - Ensure that the analysis is unbiased and provides a well-rounded view with insights into the market’s current position and future performance.

            Return Format:
            - Deep Analysis: Thorough examination of the stock based on the provided data.
            - Refined Summary: A concise, insightful overview of the stock's recent performance and market context.
            - Key Takeaways: Bullet-point insights focused on price movement, volume, trends, and key indicators.
            - Risk Warnings: Highlight potential risks with likelihood indicators (e.g., High, Medium, Low). If no specific data is available to quantify risks, state that the risk is "uncertain" or "unable to quantify."
            - Actionable Insights: Provide scenarios (bullish, bearish, neutral) based on data-driven analysis. Recommend specific targets or thresholds for action (e.g., "consider buying if price increases by X%").

            Warnings:
            - Maintain a neutral and factual tone—no financial advice or speculation.
            - Use structured, readable formatting (e.g., clear headings, bullet points).
            - Emphasize accuracy, not verbosity.
            - Dont ask to be provided with more data, conduct a professional analysis with what you have with no conversation.

            Context:
            - Include historical comparison if relevant.
            - Compare performance to sector/industry benchmarks when applicable.
            - Reference {stock_data} to find key metrics and news. If data is missing or incomplete (e.g., shares outstanding, stock price), explicitly mention this gap and suggest ways to retrieve or estimate the missing information.
            """
        },
        {
            "role": "user",
            "content": llm_response
        }
    ]
}

   # Optionally include stock data in the prompt
    if stock_data:
        try:
            # Convert to JSON string, handling datetime objects
            stock_data_json = json.dumps(stock_data, default=str, indent=2)
            payload["messages"].insert(0, {"role": "user", "content": f"Stock Data: {stock_data_json}"})
        except Exception as e:
            print(f"Debug: Error converting stock data to JSON: {str(e)}")
            stock_data_json = "Error converting stock data to JSON."

    try:
        async with httpx.AsyncClient() as client:
            # Stream the response
            async with client.stream("POST", url, json=payload, timeout=200.0) as response:
                if response.status_code == 200:
                    # Process the response using process_streaming_response
                    deepthinking_response = ""
                    async for content in process_streaming_response(response):
                        # Print each chunk as it arrives
                        print(content, end="", flush=True)
                        deepthinking_response += content
                    return deepthinking_response
                else:
                    print(
                        f"Debug: DeepThinking API response status: {response.status_code}")
                    print(
                        f"Debug: DeepThinking API response text: {response.text}")
                    raise RuntimeError(
                        f"Error {response.status_code}: {response.text}")
    except httpx.RequestError as e:
        print(f"Debug: HTTP request error: {str(e)}")
        raise RuntimeError(
            f"Failed to send data to DeepThinking model: {str(e)}")
    except Exception as e:
        print(f"Debug: General exception: {str(e)}")
        raise RuntimeError(
            f"Failed to send data to DeepThinking model: {str(e)}")


def store_analysis(symbol, analysis):
    """
    Store the analysis in the database, avoiding duplicates.
    """
    db.analyses.update_one(
        {"symbol": symbol},
        {"$set": {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }},
        upsert=True
    )


async def fetch_and_analyze_all_stock_data(ticker: str):
    try:
        logger.info("Starting stock analysis", ticker=ticker)
        print(f"Debug: Fetching and analyzing stock data for ticker: {ticker}")

        # Fetch real stock data using the stock services
        stock_data = validate_stock_data(await fetch_all_stock_data(ticker))
        logger.debug("Stock data fetched", ticker=ticker, has_metadata=bool(stock_data.get("metadata")))
        print("Debug: Fetched stock data:", stock_data)

        if not stock_data or "metadata" not in stock_data:
            print("Debug: No stock data available, using default analysis.")
            analysis = "No stock data available for analysis."
            llm_response = "No stock data available for analysis."
            deepthinking_response = "No stock data available for analysis."
        else:
            # Perform analysis on the fetched stock data
            metadata = stock_data["metadata"]
            print("Debug: Metadata:", metadata)

            analysis = perform_analysis(stock_data)
            print("Debug: Analysis result:", analysis)

            # Generate LLM response
            llm_response = await send_prompt_to_llm(analysis)
            print("Debug: LLM response:", llm_response)

            # Generate DeepThinking response
            deepthinking_response = await send_to_deepseek(llm_response, stock_data)
            print("Debug: DeepThinking response:", deepthinking_response)

        return {
            "symbol": ticker,
            "analysis": analysis,
            "llm_response": llm_response,
            "deepthinking_response": deepthinking_response,
            "stock_data": stock_data,
        }
    except Exception as e:
        print(f"Debug: Exception occurred: {e}")
        raise RuntimeError(
            f"Error in fetch_and_analyze_all_stock_data: {str(e)}")


async def process_question_with_llm(question: str, context: str = None) -> str:
    try:
        print(f"Debug: Received question: {question}")
        print(f"Debug: Received context: {context}")

        # Construct the prompt
        prompt = f"""
        You are a stock market enthusiast. Answer the following question concisely:

        Question: {question}
        """
        if context:
            prompt += f"\nContext: {context}\n"

        print(f"Debug: Constructed prompt: {prompt}")

        # Send the prompt to the LLM
        llm_response = await send_prompt_to_llm(prompt)

        print(f"Debug: LLM response: {llm_response}")
        return llm_response
    except Exception as e:
        print(f"Error in process_question_with_llm: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}")