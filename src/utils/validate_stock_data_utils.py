def validate_stock_data(stock_data):
    """
    Check to ensure that there is stock data being returned
    """
    if not stock_data:
        raise ValueError("Stock data is empty or None.")
    if "metadata" not in stock_data:
        raise KeyError("'metadata' key is missing in stock data.")
    return stock_data
