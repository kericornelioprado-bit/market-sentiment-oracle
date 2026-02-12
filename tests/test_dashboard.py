
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from src.dashboard import app

# Tests for functions (load_data, make_prediction) can now import app safely

@patch("src.dashboard.app.storage.Client")
def test_load_data(mock_client_cls):
    # Mock behavior
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_client_cls.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    # Exists case
    mock_blob.exists.return_value = True
    df_fake = pd.DataFrame({"Close": [100, 101], "Date": ["2023-01-01", "2023-01-02"]})
    import io
    buf = io.BytesIO()
    df_fake.to_parquet(buf)
    mock_blob.download_as_bytes.return_value = buf.getvalue()
    
    data = app.load_data("AAPL")
    assert isinstance(data, pd.DataFrame)
    
    # Not found case
    mock_blob.exists.return_value = False
    data = app.load_data("BAD")
    assert data is None

def test_make_prediction():
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([[0.8]])
    mock_scaler = MagicMock()
    # Feature columns: Close, Feature1 (2 cols) -> Scaler output must match
    mock_scaler.transform.return_value = np.zeros((10, 2))
    
    df = pd.DataFrame({
        "Close": np.random.rand(15), 
        "Target": np.zeros(15), 
        "date_only": np.zeros(15), 
        "Ticker": ["A"]*15, 
        "Date": np.zeros(15), 
        "Feature1": np.random.rand(15),
    })
    
    prob = app.make_prediction(mock_model, mock_scaler, df)
    assert prob == 0.8

def test_make_prediction_short():
    df = pd.DataFrame({"Close": [1]})
    assert app.make_prediction(None, None, df) == 0.5

@patch("src.dashboard.app.Path")
@patch("src.dashboard.app.tf.keras.models.load_model")
@patch("src.dashboard.app.joblib.load")
def test_load_model(mock_joblib, mock_keras, mock_path):
    # Setup Path resolution
    mock_path.return_value.resolve.return_value.joinpath.return_value.resolve.return_value = MagicMock(exists=lambda: True, is_relative_to=lambda x: True)
    
    m, s = app.load_model("AAPL")
    assert m is not None
    assert s is not None

# Test the UI flow (main)
@patch("src.dashboard.app.load_data")
@patch("src.dashboard.app.load_model")
@patch("src.dashboard.app.make_prediction")
@patch("src.dashboard.app.st") # Mock streamlit to prevent rendering
def test_main_flow(mock_st, mock_pred, mock_load_model, mock_load_data):
    # Setup mocks
    mock_st.sidebar.selectbox.return_value = "AAPL"
    
    # Mock columns unpacking
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    
    # Data
    dates = pd.date_range("2023-01-01", periods=20)
    df = pd.DataFrame({
        "Close": np.linspace(100, 110, 20),

        "Open": np.linspace(100, 110, 20),
        "High": np.linspace(100, 110, 20),
        "Low": np.linspace(100, 110, 20),
        "rsi_14": np.linspace(30, 70, 20),
        "daily_sentiment": np.linspace(-1, 1, 20),
        "bb_upper": np.linspace(105, 115, 20),
        "bb_lower": np.linspace(95, 105, 20),
        "Date": dates
    }, index=dates)
    mock_load_data.return_value = df
    
    mock_load_model.return_value = (MagicMock(), MagicMock())
    mock_pred.return_value = 0.9
    
    # Run main
    app.main()
    
    # Verify metrics called
    assert mock_st.columns.called
    assert mock_st.plotly_chart.called
