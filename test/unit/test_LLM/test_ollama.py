# import json
# import requests

# # Mock data for live market data
# mockLiveMarketData = {
#     "AAPL": {
#         "symbol": "AAPL",
#         "timestamp": "2025-03-08 16:00:00",
#         "open": 150.0,
#         "high": 155.0,
#         "low": 148.0,
#         "close": 152.0,
#         "volume": 1000000,
#         "market_cap": "3626259972000",
#         "dividend_yield": "0.0041",
#         "pe_ratio": "38.26",
#         "eps": "6.31",
#         "beta": "1.178",
#         "52_week_high": "259.81",
#         "52_week_low": "163.31",
#         "current_price": "240.22",
#         "analyst_ratings": "252.23",
#         "price_targets": "252.23",
#         "events": "0.101",
#         "about": "Apple Inc. is an American multinational technology company that specializes in consumer electronics, computer software, and online services. Apple is the world's largest technology company by revenue (totalling $274.5 billion in 2020) and, since January 2021, the world's most valuable company. As of 2021, Apple is the world's fourth-largest PC vendor by unit sales, and fourth-largest smartphone manufacturer. It is one of the Big Five American information technology companies, along with Amazon, Google, Microsoft, and Facebook."
#     },
#     "GOOGL": {
#         "symbol": "GOOGL",
#         "timestamp": "2025-03-08 16:00:00",
#         "open": 2800.0,
#         "high": 2850.0,
#         "low": 2750.0,
#         "close": 2825.0,
#         "volume": 1500000,
#         "market_cap": "1826259972000",
#         "dividend_yield": "0.0021",
#         "pe_ratio": "32.26",
#         "eps": "5.31",
#         "beta": "1.078",
#         "52_week_high": "3059.81",
#         "52_week_low": "2531.31",
#         "current_price": "2900.22",
#         "analyst_ratings": "3000.23",
#         "price_targets": "3000.23",
#         "events": "0.201",
#         "about": "Alphabet Inc. is an American multinational conglomerate headquartered in Mountain View, California. It was created through a corporate restructuring of Google on October 2, 2015, and became the parent company of Google and several former Google subsidiaries. Alphabet is the world's third-largest technology company by revenue and one of the world's most valuable companies."
#     }
# }

# # Set up the base URL for the local Ollama API
# url = "http://localhost:11434/api/chat"

# # Function to format the prompt with stock data
# def format_prompt(stock_data):
#     prompt = f"""
#     Please provide a professional financial analysis for the following stock:

#     Symbol: {stock_data['symbol']}
#     Open: {stock_data['open']}
#     High: {stock_data['high']}
#     Low: {stock_data['low']}
#     Close: {stock_data['close']}
#     Volume: {stock_data['volume']}
#     Market Cap: {stock_data['market_cap']}
#     Dividend Yield: {stock_data['dividend_yield']}
#     P/E Ratio: {stock_data['pe_ratio']}
#     EPS: {stock_data['eps']}
#     Beta: {stock_data['beta']}
#     52 Week High: {stock_data['52_week_high']}
#     52 Week Low: {stock_data['52_week_low']}
#     Current Price: {stock_data['current_price']}
#     Analyst Ratings: {stock_data['analyst_ratings']}
#     Price Targets: {stock_data['price_targets']}
#     Events: {stock_data['events']}
#     About: {stock_data['about']}

#     Should this stock be considered for long-term investment? Please explain your reasoning.
#     """
#     return prompt

# # Use mock data for a particular symbol
# symbol = "AAPL"  # Replace with the desired stock symbol
# stock_data = mockLiveMarketData

# # Extract the specific stock data
# if symbol in stock_data:
#     specific_stock_data = stock_data[symbol]
#     specific_stock_data['symbol'] = symbol
# else:
#     print(f"Error: No data found for symbol {symbol}")
#     specific_stock_data = {
#         "symbol": symbol,
#         "open": "N/A",
#         "high": "N/A",
#         "low": "N/A",
#         "close": "N/A",
#         "volume": "N/A",
#         "market_cap": "N/A",
#         "dividend_yield": "N/A",
#         "pe_ratio": "N/A",
#         "eps": "N/A",
#         "beta": "N/A",
#         "52_week_high": "N/A",
#         "52_week_low": "N/A",
#         "current_price": "N/A",
#         "analyst_ratings": "N/A",
#         "price_targets": "N/A",
#         "events": "N/A",
#         "about": "N/A"
#     }

# # Format the prompt with the stock data
# prompt = format_prompt(specific_stock_data)

# # Define the payload (your input prompt)
# payload = {
#     "model": "mistral",  # Replace with the model name you're using
#     "messages": [{"role": "user", "content": prompt}]
# }

# # Send the HTTP POST request with streaming enabled
# response = requests.post(url, json=payload, stream=True)

# # Check the response status
# if response.status_code == 200:
#     print("Streaming response from Ollama:")
#     for line in response.iter_lines(decode_unicode=True):
#         if line:  # Ignore empty lines
#             try:
#                 # Parse each line as a JSON object
#                 json_data = json.loads(line)
#                 # Extract and print the assistant's message content
#                 if "message" in json_data and "content" in json_data["message"]:
#                     print(json_data["message"]["content"], end="")
#             except json.JSONDecodeError:
#                 print(f"\nFailed to parse line: {line}")
#     print()  # Ensure the final output ends with a newline
# else:
#     print(f"Error: {response.status_code}")
#     print(response.text)