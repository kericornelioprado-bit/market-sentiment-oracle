import pandas as pd
from unittest.mock import patch, call
import os
from datetime import datetime

# Import the function to be tested
from src.data.ingest import download_market_data, OUTPUT_DIR


def create_multiindex_mock_df(tickers):
    """Helper to create a MultiIndex DataFrame like yfinance returns."""
    dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
    data = {
        (ticker, col): [100.0, 101.0]
        for ticker in tickers
        for col in ["Open", "High", "Low", "Close", "Volume"]
    }
    df = pd.DataFrame(data, index=dates)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    return df


def test_download_market_data_success():
    """
    Test successful download and saving of market data for multiple tickers using batch download.
    """
    tickers = ["TEST1", "TEST2"]
    mock_df = create_multiindex_mock_df(tickers)

    with (
        patch("src.data.ingest.yf.download", return_value=mock_df) as mock_yf_download,
        patch("src.data.ingest.os.makedirs") as mock_makedirs,
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", tickers),
    ):
        download_market_data()

        # Assert os.makedirs was called
        mock_makedirs.assert_called_once_with(OUTPUT_DIR, exist_ok=True)

        # Assert yf.download was called ONCE with the list of tickers
        assert mock_yf_download.call_count == 1
        call_args = mock_yf_download.call_args
        assert call_args[0][0] == tickers
        assert call_args.kwargs["group_by"] == "ticker"

        # Assert to_parquet was called for each ticker
        assert mock_to_parquet.call_count == len(tickers)

        today_date = datetime.now().strftime("%Y-%m-%d")
        mock_to_parquet.assert_has_calls(
            [
                call(os.path.join(OUTPUT_DIR, f"TEST1_{today_date}.parquet")),
                call(os.path.join(OUTPUT_DIR, f"TEST2_{today_date}.parquet")),
            ],
            any_order=True,
        )


def test_download_market_data_single_ticker():
    """
    Test handling when only one ticker is requested (might return flat DF depending on mocking).
    But our code handles flat DF if len(TICKERS) == 1.
    """
    tickers = ["TEST1"]
    # Mocking as flat DF to simulate single ticker behavior
    mock_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "Close": [101.0, 102.0],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )

    with (
        patch("src.data.ingest.yf.download", return_value=mock_df) as mock_yf_download,
        patch("src.data.ingest.os.makedirs"),
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", tickers),
    ):
        download_market_data()

        mock_yf_download.assert_called_once()
        mock_to_parquet.assert_called_once()
        today_date = datetime.now().strftime("%Y-%m-%d")
        mock_to_parquet.assert_called_with(
            os.path.join(OUTPUT_DIR, f"TEST1_{today_date}.parquet")
        )


def test_download_market_data_no_data():
    """
    Test handling when yfinance returns an empty DataFrame (batch).
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
        mock_to_parquet.assert_not_called()


def test_download_market_data_exception():
    """
    Test error handling during yfinance batch download.
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
        mock_to_parquet.assert_not_called()

def test_download_market_data_partial_missing():
    """
    Test when one ticker is missing from the batch result.
    """
    tickers = ["FOUND", "MISSING"]
    # Mock only contains FOUND
    mock_df = create_multiindex_mock_df(["FOUND"])

    with (
        patch("src.data.ingest.yf.download", return_value=mock_df),
        patch("src.data.ingest.os.makedirs"),
        patch("pandas.DataFrame.to_parquet") as mock_to_parquet,
        patch("src.data.ingest.TICKERS", tickers),
    ):
        download_market_data()

        assert mock_to_parquet.call_count == 1
        today_date = datetime.now().strftime("%Y-%m-%d")
        mock_to_parquet.assert_called_with(
            os.path.join(OUTPUT_DIR, f"FOUND_{today_date}.parquet")
        )
