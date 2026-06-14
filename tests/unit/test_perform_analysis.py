from src.LLM.LLM_service import perform_analysis


def make_sample_stock():
    return {
        "metadata": {
            "ticker": "TEST",
            "current_price": "100",
            "industry": "Technology",
        },
        "historical_data": {
            "historical_data": [
                {"close": "100", "high": "105", "low": "95", "volume": 1000000},
                {"close": "102", "high": "106", "low": "96", "volume": 1100000},
                {"close": "101", "high": "107", "low": "97", "volume": 900000},
                {"close": "99", "high": "103", "low": "94", "volume": 1200000},
                {"close": "98", "high": "102", "low": "93", "volume": 800000},
            ]
        },
        "income_statement": {"annual_reports": [{"netIncome": "1000000", "totalRevenue": "5000000"}]},
        "balance_sheet": {"annual_reports": [{"commonStockSharesOutstanding": "10000", "totalAssets": "2000000", "totalShareholderEquity": "1500000", "shortLongTermDebtTotal": "100000"}]},
        "cash_flow": {"annual_reports": [{"operatingCashflow": "300000", "dividendPayout": "0", "dividendPayoutCommonStock": "0"}]},
        "sma": {},
        "ema": {},
        "news": [],
    }


def test_perform_analysis_contains_expected_fields():
    stock = make_sample_stock()
    result = perform_analysis(stock)

    assert "Ticker: TEST" in result
    assert "Current Price: $100" in result
    # EPS should be computed
    assert "EPS:" in result
    # SMA was calculated from recent prices
    assert "Simple Moving Average" in result or "Simple Moving Average (5-day)" in result
