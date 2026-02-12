
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch
from src.features import merge_data

# Create a dummy class to test process_sentiment_aggregation isolation
class DummyMerger(merge_data.DataMerger):
    def __init__(self):
        # Skip init
        pass

@pytest.fixture
def merger():
    return DummyMerger()

def test_process_sentiment_aggregation_temporal_shift(merger):
    data = {
        "publishedAt": [
            "2023-01-01T20:59:00Z", 
            "2023-01-01T21:01:00Z", 
            "2023-01-02T10:00:00Z"
        ],
        "sentiment_label": ["positive", "negative", "positive"],
        "sentiment_score": [0.9, 0.8, 0.7],
        "title": ["A", "B", "C"]
    }
    df_sentiment = pd.DataFrame(data)
    
    result = merger.process_sentiment_aggregation(df_sentiment)
    
    # Check Jan 1
    row_jan1 = result[result["date_only"] == pd.Timestamp("2023-01-01")]
    assert len(row_jan1) == 1
    assert np.isclose(row_jan1["daily_sentiment"].values[0], 0.9)
    
    # Check Jan 2
    row_jan2 = result[result["date_only"] == pd.Timestamp("2023-01-02")]
    assert len(row_jan2) == 1
    assert np.isclose(row_jan2["daily_sentiment"].values[0], -0.05)

def test_process_sentiment_aggregation_empty(merger):
    df = pd.DataFrame()
    res = merger.process_sentiment_aggregation(df)
    assert res.empty

def test_process_sentiment_aggregation_missing_cols(merger):
    df = pd.DataFrame({"foo": [1]})
    res = merger.process_sentiment_aggregation(df)
    assert res.empty

@patch("src.features.merge_data.glob.glob")
@patch("src.features.merge_data.pd.read_parquet")
@patch("src.features.merge_data.add_technical_features")
@patch("src.features.merge_data.DataMerger.load_parquet_from_gcs")
@patch("src.features.merge_data.DataMerger.process_sentiment_aggregation")
@patch("src.features.merge_data.pd.DataFrame.to_parquet")
@patch("src.features.merge_data.os") # Patch entire OS module imported in merge_data
def test_merger_run_pipeline_flow(mock_os, mock_to_parquet, mock_process, mock_load_gcs, mock_tech, mock_read_parquet, mock_glob, merger):
    # Setup mocks
    mock_glob.return_value = ["data/raw/AAPL_2023.parquet"]
    
    # Configure mock_os to handle getmtime
    # merge_data calls max(..., key=os.path.getmtime)
    # mock_os.path.getmtime needs to be callable
    mock_os.path.getmtime.return_value = 1000.0
    mock_os.makedirs.return_value = None
    
    df_price = pd.DataFrame({"Close": [100]}, index=pd.to_datetime(["2023-01-01"]))
    mock_read_parquet.return_value = df_price
    mock_tech.return_value = df_price # Return same
    
    df_sentiment = pd.DataFrame({"date_only": [pd.Timestamp("2023-01-01")]})
    mock_load_gcs.return_value = df_sentiment
    
    mock_process.return_value = pd.DataFrame({
        "date_only": [pd.Timestamp("2023-01-01")], 
        "daily_sentiment": [0.5],
        "news_volume": [1]
    })
    
    merger.tickers = ["AAPL"]
    merger.bucket = MagicMock()
    merger.storage_client = MagicMock()
    
    merger.run_pipeline()
    
    assert mock_to_parquet.called

@patch("src.features.merge_data.DataMerger.run_pipeline")
@patch("src.features.merge_data.storage.Client")
def test_merger_main(mock_client, mock_run_pipeline):
    # Test instantiation
    merger = merge_data.DataMerger("bucket", ["AAPL"])
    merger.run_pipeline()
    assert mock_run_pipeline.called

@patch("src.features.merge_data.DataMerger.run_pipeline")
@patch("src.features.merge_data.storage.Client")
def test_main_execution(mock_client, mock_run_pipeline):
    merge_data.main()
    assert mock_run_pipeline.called
