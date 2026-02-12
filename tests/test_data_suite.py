
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
from src.data import ingest, ingest_news
from datetime import datetime

# --- Tests for src/data/ingest.py ---

@patch("src.data.ingest.yf.download")
@patch("src.data.ingest.os.makedirs")
@patch("pandas.DataFrame.to_parquet")
def test_download_market_data_success(mock_to_parquet, mock_makedirs, mock_yf_download):
    # Mock yfinance data
    mock_df = pd.DataFrame({
        ("AAPL", "Close"): [150.0, 151.0],
        ("AAPL", "Open"): [149.0, 150.0],
        ("MSFT", "Close"): [250.0, 251.0],
        ("MSFT", "Open"): [249.0, 250.0],
    })
    # Set columns to MultiIndex as yfinance does with group_by='ticker'
    mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)
    mock_yf_download.return_value = mock_df

    ingest.download_market_data()

    # Verify os.makedirs called
    mock_makedirs.assert_called_with("data/raw", exist_ok=True)
    
    # Verify yf.download called
    mock_yf_download.assert_called()

    # Verify to_parquet called for AAPL and MSFT
    assert mock_to_parquet.called

@patch("src.data.ingest.yf.download")
def test_download_market_data_exception(mock_yf_download):
    mock_yf_download.side_effect = Exception("Download failed")
    # Should handle exception and print error, not crash
    ingest.download_market_data()

# --- Tests for src/data/ingest_news.py ---

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("NEWS_API_KEY", "test_key")
    monkeypatch.setenv("GCS_BUCKET_NAME", "test_bucket")

@patch("src.data.ingest_news.requests.get")
@patch("src.data.ingest_news.upload_to_gcs")
@patch("pandas.DataFrame.to_parquet")
def test_fetch_news_success(mock_to_parquet, mock_upload, mock_get, mock_env_vars):
    # Ensure API KEY is set in the module (it might have been imported as None)
    with patch("src.data.ingest_news.API_KEY", "test_key"):
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [
                {
                    "publishedAt": "2023-01-01T10:00:00Z",
                    "title": "Test News",
                    "url": "http://example.com",
                    "content": "Content",
                    "source": {"name": "Test Source"}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        ingest_news.fetch_news(symbols=["AAPL"])

        assert mock_get.called
        assert mock_to_parquet.called
        assert mock_upload.called

@patch("src.data.ingest_news.requests.get")
def test_fetch_news_api_error(mock_get, mock_env_vars):
    with patch("src.data.ingest_news.API_KEY", "test_key"):
        mock_get.side_effect = ingest_news.requests.exceptions.RequestException("API Error")
        # Should handle exception smoothly
        ingest_news.fetch_news(symbols=["AAPL"])

def test_fetch_news_no_api_key():
    # Patch the module-level variable to None to simulate missing key
    with patch("src.data.ingest_news.API_KEY", None):
        with pytest.raises(ValueError, match="No se encontró la API Key"):
            ingest_news.fetch_news()

# Test Schema Validation
def test_news_schema_validation():
    df = pd.DataFrame({
        "publishedAt": [datetime.now()],
        "title": ["Valid Title"],
        "url": ["http://valid.url"],
        "content": ["Some content"],
        "symbol": ["AAPL"],
        "fetched_at": [datetime.now()]
    })
    validated_df = ingest_news.NewsArticleSchema.validate(df)
    assert validated_df is not None

def test_news_schema_invalid_url():
    df = pd.DataFrame({
        "publishedAt": [datetime.now()],
        "title": ["Valid Title"],
        "url": ["invalid_url"], # Missing http
        "content": ["Some content"],
        "symbol": ["AAPL"],
        "fetched_at": [datetime.now()]
    })
    with pytest.raises(ingest_news.SchemaError):
         ingest_news.NewsArticleSchema.validate(df)
