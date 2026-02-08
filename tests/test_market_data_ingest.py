import pandas as pd
import yfinance as yf
from unittest.mock import patch, MagicMock, call
import os
from datetime import datetime

# Import the function to be tested
from src.data.ingest import download_market_data, TICKERS, OUTPUT_DIR


# Test cases
def test_download_market_data_success():
    """
    Test successful download and saving of market data for multiple tickers using batch download.
    """
    # Mock yfinance.download to return a dummy MultiIndex DataFrame (as if group_by='ticker' was used)
    # yfinance batch download with group_by='ticker' returns columns like (Ticker, PriceType)
    # but pandas stores MultiIndex as tuples in columns if defined this way.

    dates = pd.to_datetime(["2024-01-01", "2024-01-02"])

    # Create MultiIndex columns
    columns = pd.MultiIndex.from_tuples([
        ("TEST1", "Open"), ("TEST1", "High"), ("TEST1", "Low"), ("TEST1", "Close"), ("TEST1", "Volume"),
        ("TEST2", "Open"), ("TEST2", "High"), ("TEST2", "Low"), ("TEST2", "Close"), ("TEST2", "Volume"),
    ], names=["Ticker", "Price"])

    data = [
        [100.0, 102.0, 99.0, 101.0, 1000, 200.0, 202.0, 199.0, 201.0, 2000],
        [101.0, 103.0, 100.0, 102.0, 1100, 201.0, 203.0, 200.0, 202.0, 2100]
    ]

    mock_df = pd.DataFrame(data, index=dates, columns=columns)

    with (
        patch("src.data.ingest.yf.download", return_value=mock_df) as mock_yf_download,
        patch("src.data.ingest.os.makedirs") as mock_makedirs,
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", ["TEST1", "TEST2"]),
    ):
        download_market_data()

        # Assert os.makedirs was called
        mock_makedirs.assert_called_once_with(OUTPUT_DIR, exist_ok=True)

        # Assert yf.download was called ONCE with the list of tickers
        # Note: We can't easily check start/end dates exactly if they are dynamic inside the function,
        # but we can check the tickers list.
        # Check call arguments
        args, kwargs = mock_yf_download.call_args
        assert args[0] == ["TEST1", "TEST2"]
        assert kwargs["group_by"] == "ticker"
        assert kwargs["progress"] == False

        # Assert to_parquet was called for each ticker (2 times)
        assert mock_to_parquet.call_count == 2

        # Verify file names
        today_date = datetime.now().strftime("%Y-%m-%d")
        mock_to_parquet.assert_has_calls(
            [
                call(os.path.join(OUTPUT_DIR, f"TEST1_{today_date}.parquet")),
                call(os.path.join(OUTPUT_DIR, f"TEST2_{today_date}.parquet")),
            ],
            any_order=True,
        )


def test_download_market_data_no_data():
    """
    Test handling when yfinance returns an empty DataFrame (e.g. all NaNs or empty).
    """
    # If batch download returns empty DF
    with (
        patch(
            "src.data.ingest.yf.download", return_value=pd.DataFrame()
        ) as mock_yf_download,
        patch("src.data.ingest.os.makedirs"),
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", ["EMPTY_TICKER"]),
    ):
        download_market_data()

        mock_yf_download.assert_called_once()
        mock_to_parquet.assert_not_called()  # No data, so no parquet file should be saved


def test_download_market_data_exception():
    """
    Test error handling during yfinance download.
    """
    with (
        patch(
            "src.data.ingest.yf.download", side_effect=Exception("Network Error")
        ) as mock_yf_download,
        patch("src.data.ingest.os.makedirs"),
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", ["ERROR_TICKER"]),
    ):
        download_market_data()

        mock_yf_download.assert_called_once()
        mock_to_parquet.assert_not_called()  # Error, so no parquet file should be saved
