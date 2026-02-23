# from unittest.mock import patch, AsyncMock
# import pytest
# from src.alphaVantage.services.stock_services import fetch_all_stock_data
# from src.LLM.LLM_service import (
#     perform_analysis,
#     fetch_and_analyze_all_stock_data,
#     send_prompt_to_llm,
#     send_to_deepseek,
# )

# class TestIndividualEndpoints:
#     @pytest.mark.asyncio
#     async def test_fetch_all_stock_data(self):
#         ticker = "AAPL"
#         stock_data = await fetch_all_stock_data(ticker)
#         assert stock_data is not None, "Stock data should not be None"
#         print("Fetched stock data:", stock_data)

#     def test_perform_analysis(self):
#         metadata = {
#             "ticker": "AAPL",
#             "industry": "ELECTRONIC COMPUTERS",
#             "market_cap": "3278873821000",
#             "dividend_yield": "0.0046",
#             "pe_ratio": "34.59",
#             "eps": "6.31",
#             "beta": "1.178",
#             "52_week_high": "259.81",
#             "52_week_low": "163.31",
#             "current_price": "231.92",
#             "analyst_ratings": "252.59",
#         }
#         analysis = perform_analysis({"metadata": metadata})
#         assert "Metadata" in analysis, "Analysis should include 'Metadata'"
#         print("Analysis result:", analysis)

#     @pytest.mark.asyncio
#     async def test_send_prompt_to_llm(self):
#         prompt = """
#         Analyze the following stock data:

#         Metadata: {
#             "ticker": "AAPL",
#             "industry": "ELECTRONIC COMPUTERS",
#             "market_cap": "3278873821000",
#             "dividend_yield": "0.0046",
#             "pe_ratio": "34.59",
#             "eps": "6.31",
#             "beta": "1.178",
#             "52_week_high": "259.81",
#             "52_week_low": "163.31",
#             "current_price": "231.92",
#             "analyst_ratings": "252.59"
#         }
#         """
#         response = await send_prompt_to_llm(prompt)
#         assert response is not None, "LLM response should not be None"
#         print("LLM response:", response)

#     @pytest.mark.asyncio
#     async def test_send_to_deepseek(self):
#         llm_response = "Sample LLM response for TSLA."
#         response = await send_to_deepseek(llm_response)
#         assert response is not None, "DeepThinking response should not be None"
#         print("DeepThinking response:", response)

# # Testing output response
#     @pytest.mark.asyncio
#     async def test_fetch_and_analyze_all_stock_data(self):
#         ticker = "AAPL"  # Example ticker symbol
#         result = await fetch_and_analyze_all_stock_data(ticker)
#         assert "symbol" in result, "Result should contain 'symbol'"
#         assert "analysis" in result, "Result should contain 'analysis'"
#         assert "llm_response" in result, "Result should contain 'llm_response'"
#         assert "deepthinking_response" in result, "Result should contain 'deepthinking_response'"
#         assert "stock_data" in result, "Result should contain 'stock_data'"
#         print("Fetch and analyze result:", result)

# # Mocking both LLM response to check if being passed
# @pytest.mark.asyncio
# @patch("src.LLM.LLM_service.send_prompt_to_llm", new_callable=AsyncMock)
# @patch("src.LLM.LLM_service.send_to_deepseek", new_callable=AsyncMock)
# async def test_fetch_and_analyze_all_stock_data_mock(mock_send_to_deepseek, mock_send_prompt_to_llm):
#     # Mock the responses
#     mock_send_prompt_to_llm.return_value = "Mock LLM response"
#     mock_send_to_deepseek.return_value = "Mock DeepThinking response"

#     ticker = "AAPL"  # Example ticker symbol
#     result = await fetch_and_analyze_all_stock_data(ticker)
#     assert "symbol" in result, "Result should contain 'symbol'"
#     assert "analysis" in result, "Result should contain 'analysis'"
#     assert "llm_response" in result, "Result should contain 'llm_response'"
#     assert "deepthinking_response" in result, "Result should contain 'deepthinking_response'"
#     assert "stock_data" in result, "Result should contain 'stock_data'"
#     print("Fetch and analyze result:", result)