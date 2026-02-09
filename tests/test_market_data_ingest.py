import pandas as pd
from unittest.mock import patch, call
import os
from datetime import datetime

# Import the function to be tested
from src.data.ingest import download_market_data, OUTPUT_DIR


# Test cases
def test_download_market_data_success():
    """
    Test successful download and saving of market data for multiple tickers using batch download.
    """
    # Create mock MultiIndex DataFrame
    tickers = ["TEST1", "TEST2"]
    metrics = ["Open", "High", "Low", "Close", "Volume"]
    columns = pd.MultiIndex.from_product([tickers, metrics], names=["Ticker", "Price"])

    dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
    # Create a DataFrame with some data
    mock_df = pd.DataFrame(100.0, index=dates, columns=columns)

    with (
        patch("src.data.ingest.yf.download", return_value=mock_df) as mock_yf_download,
        patch("src.data.ingest.os.makedirs") as mock_makedirs,
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", tickers),
    ):
        download_market_data()

        # Assert os.makedirs was called
        mock_makedirs.assert_called_once_with(OUTPUT_DIR, exist_ok=True)

        # Assert yf.download was called ONCE with ALL tickers (batch mode)
        mock_yf_download.assert_called_once()
        args, kwargs = mock_yf_download.call_args

        # Verify arguments passed to yf.download
        # tickers argument (args[0]) might be a list or tuple
        assert set(args[0]) == set(tickers)
        assert kwargs.get("group_by") == "ticker"
        assert kwargs.get("progress") is False

        # Assert to_parquet was called for each ticker (2 times)
        assert mock_to_parquet.call_count == len(tickers)

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
    Test handling when yfinance returns an empty DataFrame.
    """
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


def test_download_market_data_single_ticker_df():
    """
    Test edge case where yfinance returns a simple DataFrame (not MultiIndex) for a single ticker.
    """
    mock_df = pd.DataFrame(
        {"Open": [100.0], "Close": [102.0]},
        index=pd.to_datetime(["2024-01-01"])
    )

    with (
        patch(
            "src.data.ingest.yf.download", return_value=mock_df
        ) as mock_yf_download,
        patch("src.data.ingest.os.makedirs"),
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", ["SINGLE_TICKER"]),
    ):
        download_market_data()

        mock_yf_download.assert_called_once()
        mock_to_parquet.assert_called_once() # Should be saved


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
