import pytest

from src.utils.validate_stock_data_utils import validate_stock_data


def test_validate_stock_data_success():
    data = {"metadata": {"ticker": "AAPL"}}
    assert validate_stock_data(data) is data


def test_validate_stock_data_empty():
    with pytest.raises(ValueError):
        validate_stock_data(None)


def test_validate_stock_data_missing_metadata():
    with pytest.raises(KeyError):
        validate_stock_data({"no_meta": True})
