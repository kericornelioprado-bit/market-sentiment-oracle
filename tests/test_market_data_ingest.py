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
    Test successful download and saving of market data for multiple tickers.
    """
    # Mock yfinance.download to return a dummy DataFrame
    mock_df = pd.DataFrame({
        'Open': [100.0, 101.0],
        'High': [102.0, 103.0],
        'Low': [99.0, 100.0],
        'Close': [101.0, 102.0],
        'Volume': [1000, 1100]
    }, index=pd.to_datetime(['2024-01-01', '2024-01-02']))

    with (
        patch('src.data.ingest.yf.download', return_value=mock_df) as mock_yf_download,
        patch('src.data.ingest.os.makedirs') as mock_makedirs,
        patch('pandas.DataFrame.to_parquet') as mock_to_parquet,
        patch('src.data.ingest.TICKERS', ['TEST1', 'TEST2'])
    ):
        download_market_data()

        # Assert os.makedirs was called
        mock_makedirs.assert_called_once_with(OUTPUT_DIR, exist_ok=True)

        # Assert yf.download was called for each ticker
        expected_calls = [
            call('TEST1', start=mock_yf_download.call_args_list[0].kwargs['start'], end=mock_yf_download.call_args_list[0].kwargs['end'], progress=False),
            call('TEST2', start=mock_yf_download.call_args_list[1].kwargs['start'], end=mock_yf_download.call_args_list[1].kwargs['end'], progress=False)
        ]
        # We need to ignore start and end dates for comparison as they are dynamic
        assert mock_yf_download.call_count == len(['TEST1', 'TEST2'])
        
        # Assert to_parquet was called for each ticker
        assert mock_to_parquet.call_count == len(['TEST1', 'TEST2'])
        
        # Verify file names (can be more specific if needed)
        today_date = datetime.now().strftime('%Y-%m-%d')
        mock_to_parquet.assert_has_calls([
            call(os.path.join(OUTPUT_DIR, f'TEST1_{today_date}.parquet')),
            call(os.path.join(OUTPUT_DIR, f'TEST2_{today_date}.parquet'))
        ], any_order=True)

def test_download_market_data_no_data():
    """
    Test handling when yfinance returns an empty DataFrame.
    """
    with (
        patch('src.data.ingest.yf.download', return_value=pd.DataFrame()) as mock_yf_download,
        patch('src.data.ingest.os.makedirs'),
        patch('pandas.DataFrame.to_parquet') as mock_to_parquet,
        patch('src.data.ingest.TICKERS', ['EMPTY_TICKER'])
    ):
        download_market_data()

        mock_yf_download.assert_called_once()
        mock_to_parquet.assert_not_called() # No data, so no parquet file should be saved

def test_download_market_data_exception():
    """
    Test error handling during yfinance download.
    """
    with (
        patch('src.data.ingest.yf.download', side_effect=Exception("Network Error")) as mock_yf_download,
        patch('src.data.ingest.os.makedirs'),
        patch('pandas.DataFrame.to_parquet') as mock_to_parquet,
        patch('src.data.ingest.TICKERS', ['ERROR_TICKER'])
    ):
        download_market_data()

        mock_yf_download.assert_called_once()
        mock_to_parquet.assert_not_called() # Error, so no parquet file should be saved
