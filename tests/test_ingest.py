import os
import pandas as pd
import pandera as pa
import pytest
from unittest.mock import MagicMock, patch, mock_open, call

# Modules to test
from src.data.ingest_news import (
    NewsArticleSchema,
    fetch_news,
    upload_to_gcs as ingest_upload,
)


# Define a valid DataFrame for NewsArticleSchema
def create_valid_news_df():
    return pd.DataFrame(
        {
            "publishedAt": pd.to_datetime(["2024-01-01T12:00:00Z"]),
            "title": ["Valid News Title"],
            "url": ["http://example.com/news"],
            "content": ["Some content here."],
            "symbol": ["TEST"],
            "fetched_at": pd.to_datetime(["2024-01-02T00:00:00Z"]),
        }
    )


# --- Tests for src.data.ingest_news ---


def test_newsarticleschema_valid():
    """Test that NewsArticleSchema validates a correct DataFrame."""
    df = create_valid_news_df()
    validated_df = NewsArticleSchema.validate(df)
    assert not validated_df.empty


def test_newsarticleschema_invalid_title():
    """Test that NewsArticleSchema fails for an empty title."""
    df = create_valid_news_df()
    df["title"] = " "  # Invalid title
    with pytest.raises(pa.errors.SchemaError):
        NewsArticleSchema.validate(df)


def test_newsarticleschema_invalid_url():
    """Test that NewsArticleSchema fails for an invalid URL."""
    df = create_valid_news_df()
    df["url"] = "invalid-url"  # Invalid URL
    with pytest.raises(pa.errors.SchemaError):
        NewsArticleSchema.validate(df)


@patch("src.data.ingest_news.API_KEY", "test-key")
@patch("src.data.ingest_news.requests.get")
@patch("src.data.ingest_news.upload_to_gcs")
@patch("src.data.ingest_news.os.makedirs")
@patch("pandas.DataFrame.to_parquet")
def test_fetch_news_success(mock_to_parquet, mock_makedirs, mock_upload, mock_get):
    """Test successful news fetching and processing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "articles": [
            {
                "publishedAt": "2024-01-01T12:00:00Z",
                "title": "Test Title",
                "url": "http://example.com",
                "content": "Test content.",
            }
        ]
    }
    mock_get.return_value = mock_response

    fetch_news()

    assert mock_get.call_count == 7
    assert mock_upload.call_count == 7
    mock_makedirs.assert_called_once()
    assert mock_to_parquet.call_count == 7


@patch("src.data.ingest_news.API_KEY", "test-key")
@patch("src.data.ingest_news.requests.get")
def test_fetch_news_api_no_articles(mock_get):
    """Test fetch_news when the API returns no articles."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"articles": []}
    mock_get.return_value = mock_response

    # This should run without errors
    fetch_news(symbols=["NO_NEWS"])
    mock_get.assert_called_once()


@patch("src.data.ingest_news.requests.get")
def test_fetch_news_no_api_key(mock_get):
    """Test that fetch_news raises ValueError if API_KEY is not set."""
    with patch("src.data.ingest_news.API_KEY", None):
        with pytest.raises(ValueError, match="No se encontró la API Key"):
            fetch_news()


@patch("src.data.ingest_news.API_KEY", "test-key")
@patch("src.data.ingest_news.requests.get")
def test_fetch_news_schema_error(mock_get):
    """Test that fetch_news handles a SchemaError gracefully."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "articles": [
            {
                "publishedAt": "2024-01-01T12:00:00Z",
                "title": None,  # Invalid title to trigger SchemaError
                "url": "http://example.com",
                "content": "Test content.",
            }
        ]
    }
    mock_get.return_value = mock_response

    # The function should catch the exception and continue without error
    fetch_news(symbols=["TEST"])
    mock_get.assert_called_once()


@patch("src.data.ingest_news.get_storage_client")
def test_ingest_upload_to_gcs_success(mock_get_client):
    """Test successful file upload to GCS."""
    mock_storage_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_get_client.return_value = mock_storage_client
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    with patch("src.data.ingest_news.BUCKET_NAME", "fake-bucket"):
        ingest_upload("local/file.txt", "remote/blob.txt")

    mock_bucket.blob.assert_called_with("remote/blob.txt")
    mock_blob.upload_from_filename.assert_called_with("local/file.txt")


@patch("src.data.ingest_news.get_storage_client")
def test_ingest_upload_to_gcs_failure(mock_get_client):
    """Test failure in file upload to GCS."""
    mock_storage_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_get_client.return_value = mock_storage_client
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_blob.upload_from_filename.side_effect = Exception("Upload failed")

    with patch("src.data.ingest_news.BUCKET_NAME", "fake-bucket"):
        ingest_upload("local/file.txt", "remote/blob.txt")

        mock_blob.upload_from_filename.assert_called_with("local/file.txt")


@patch("src.data.ingest_news.storage.Client")
def test_get_storage_client_reuse(mock_client):
    """Test that the storage client is reused on subsequent calls."""

    # Since _storage_client is a global, we need to reset it

    from src.data import ingest_news

    ingest_news._storage_client = None

    client1 = ingest_news.get_storage_client()

    client2 = ingest_news.get_storage_client()

    mock_client.assert_called_once()

    assert client1 is client2


@patch("src.data.ingest_news.BUCKET_NAME", None)
def test_ingest_upload_to_gcs_no_bucket_name():
    """Test that upload skips if BUCKET_NAME is not defined."""

    ingest_upload("local/file.txt", "remote/blob.txt")

    # No mocks should be called, and no error should be raised
