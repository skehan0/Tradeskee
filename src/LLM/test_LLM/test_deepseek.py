import json
import requests

# Define the analysis
analysis = """
Here's my analysis:

1. Market Cap: A market cap of $3,626,259,972,000 indicates that the company is large and well-established in its industry. The size of the company can provide stability and reduce risk compared to smaller companies.

2. Dividend Yield: A dividend yield of 0.0041% suggests that there may not be significant income generation from this stock, but it's important to note that Apple has been reinvesting most of its profits to drive growth and innovation in their product lineup.

3. P/E Ratio: A P/E ratio of 38.26 indicates that the market is pricing the company at a premium compared to other companies in the industry. This could suggest potential for future growth, as investors are willing to pay a higher price now due to optimism about Apple's prospects. However, it's essential to consider this risk when making investment decisions.

4. EPS: A strong Earnings Per Share (EPS) of 6.31 indicates the company is earning substantial profits per share of stock outstanding. This can be a positive sign for long-term investors.

5. Beta: A beta of 1.178 suggests that Apple's stock price is more volatile than the overall market, which means it tends to experience greater price movements in response to market movements. However, this volatility may also offer opportunities for capital gains if you can successfully time your investments or ride out periods of market downturn.

6. 52 Week High and Low: The range between the 52-week high (259.81) and low (163.31) indicates a significant swing in price, which can create opportunities for long-term investors to buy at lower prices during market downturns.

7. Analyst Ratings and Price Targets: With an average analyst rating of 252.23 (on a scale from 1 to 5 where 1 is Strong Buy, 3 is Hold, and 5 is Sell) and a price target of 252.23, analysts generally view Apple as a strong buy with expectations for future growth. However, it's essential to remember that analyst ratings are not always accurate and should be used as part of your overall analysis.

8. Events: The absence of notable events suggests that there may not be any immediate catalysts driving the stock price. This could mean a more stable investment environment but also less potential for rapid price movements.

In conclusion, Apple Inc. (AAPL) appears to have strong fundamentals and growth prospects, making it a suitable candidate for long-term investment. However, investors should be aware of the higher volatility associated with this stock and consider diversifying their portfolio to mitigate risk. As always, it's essential to conduct thorough research and consult with a financial advisor before making any investment decisions.
"""

# Set up the base URL for the DeepSeek API
url = "http://localhost:11434/api/chat"

# Define the payload (your input prompt)
payload = {
    "model": "deepseek-r1:1.5b",  # Replace with the model name you're using
    "messages": [{"role": "user", "content": analysis}]
}

# Send the HTTP POST request with streaming enabled
response = requests.post(url, json=payload, stream=True)

# Check the response status
if response.status_code == 200:
    print("Streaming response from DeepSeek:")
    for line in response.iter_lines(decode_unicode=True):
        if line:  # Ignore empty lines
            try:
                # Parse each line as a JSON object
                json_data = json.loads(line)
                # Extract and print the assistant's message content
                if "message" in json_data and "content" in json_data["message"]:
                    print(json_data["message"]["content"], end="")
            except json.JSONDecodeError:
                print(f"\nFailed to parse line: {line}")
    print()  # Ensure the final output ends with a newline
else:
    print(f"Error: {response.status_code}")
    print(response.text)