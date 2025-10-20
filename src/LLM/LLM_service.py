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

# Load environment variables from .env file
load_dotenv()

# MongoDB setup
client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client.tradely


def perform_analysis(stock_data: dict) -> str:
    """
    Perform analysis on the stock data and return a formatted prompt.
    """
    
    # Define the sections to analyze
    sections = [
        "Price Data",
        "Technical Indicators", 
        "Market Sentiment",
        "Financial Metrics",
        "Risk Factors"
    ]
    
    analysis = f"""
    Goal: Conduct a concise financial analysis of {stock_data.get('metadata', {}).get('symbol', 'UNKNOWN')} based on recent market trends, historical data, and technical indicators.

    Return Format:
        - Summary: A brief overview of the stock's current trend.
        - Key Financial Indicators: Price movements, moving averages (SMA/EMA).
        - Market Sentiment: A summary of recent news and sentiment trends.
        - Risk Factors: Highlight any volatility, earnings reports, or macroeconomic risks.

    Warnings:
        - Do not provide direct financial advice.
        - Ensure the response is fact-based and avoids speculation.
        - Keep the response concise, focusing on actionable insights without exceeding 2000 words.

    Context:
        - Stock Data: {stock_data}
        - Technical Indicators: Provide insights based on available technical data.
        - Sentiment Analysis: Summarize the sentiment around recent news articles.
        - Macroeconomic Trends: Highlight broader economic influences impacting this stock.
    """

    for section in sections:
        data = stock_data.get(section.lower().replace(" ", "_"), "No data available")
        analysis += f"\n{section}: {data}"
    
    analysis += "\nThis is a preliminary Artificial Intelligence (AI) analysis. Please consult a financial advisor for investment decisions."
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

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=1000.0)

            if response.status_code == 200:
                llm_response = ""
                async for content in process_streaming_response(response):
                    # Print each chunk as it arrives
                    print(content, end="", flush=True)
                    llm_response += content
                return llm_response
            else:
                raise RuntimeError(
                    f"Error {response.status_code}: {response.text}")
    except httpx.RequestError as e:
        raise RuntimeError(f"HTTP request failed: {str(e)}")
    except Exception as e:
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

        payload["messages"].insert(
            0, {"role": "user", "content": f"Stock Data: {stock_data}"})

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
        print(f"Debug: Fetching and analyzing stock data for ticker: {ticker}")

        # Fetch real stock data using the stock services
        stock_data = validate_stock_data(await fetch_all_stock_data(ticker))
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
