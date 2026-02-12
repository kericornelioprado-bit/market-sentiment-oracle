
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.models import train_lstm, train_svm

# --- Tests for LSTMTrainer ---

@pytest.fixture
def lstm_trainer():
    with patch("src.models.train_lstm.storage.Client"):
        trainer = train_lstm.LSTMTrainer(bucket_name="test-bucket")
        return trainer

def test_lstm_create_sequences(lstm_trainer):
    # Create simple data: 0 to 19 (20 items)
    data = np.array([[i] for i in range(20)])
    target = np.array([i for i in range(20)])
    
    seq_length = 5
    X_seq, y_seq = lstm_trainer.create_sequences(data, target, time_steps=seq_length)
    
    # X_windows: [0..4] ... [15..19] -> 16 windows
    # X_seq = windows[:-1] -> 15 samples
    # y_seq = target[5:] -> 15 samples (indices 5 to 19)
    # Actually, let's verify exact logic from source
    # X_windows = sliding_window_view(X, time_steps, axis=0) -> 16 items
    # X_seq = X_windows[:-1] -> 15 items
    # y_seq = y[time_steps:] -> y[5:] -> 15 items
    
    assert len(X_seq) == len(y_seq)
    assert X_seq.shape[1] == seq_length
    assert X_seq.shape[2] == 1 # 1 feature

@patch("src.models.train_lstm.joblib.dump")
@patch("src.models.train_lstm.LSTMTrainer.load_data")
@patch("src.models.train_lstm.Sequential")
def test_lstm_train(mock_sequential, mock_load_data, mock_joblib_dump, lstm_trainer):
    # Mock Data
    dates = pd.date_range(start="2023-01-01", periods=100)
    df = pd.DataFrame({
        "Close": np.arange(100, dtype=float),
        "Open": np.arange(100, dtype=float),
        "High": np.arange(100, dtype=float),
        "Low": np.arange(100, dtype=float),
        "Volume": np.arange(100, dtype=float),
        "Ticker": ["AAPL"]*100,
        "date_only": dates
    })
    mock_load_data.return_value = df
    
    # Mock Model
    mock_model = MagicMock()
    # Mock evaluate return value [loss, accuracy]
    mock_model.evaluate.return_value = [0.1, 0.95]
    mock_sequential.return_value = mock_model
    
    lstm_trainer.train("AAPL")
    
    assert mock_model.fit.called
    assert mock_model.save.called

# --- Tests for SVMTrainer ---

@pytest.fixture
def svm_trainer():
    with patch("src.models.train_svm.storage.Client"):
        trainer = train_svm.SVMTrainer(bucket_name="test-bucket")
        return trainer

def test_svm_prepare_features(svm_trainer):
    df = pd.DataFrame({
        "Close": [100, 101, 102],
        "Open": [100, 101, 102],
        "High": [100, 101, 102],
        "Low": [100, 101, 102],
        "Volume": [100, 101, 102],
        "Ticker": ["A", "A", "A"],
        "date_only": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "Feature1": [1, 2, 3] 
    })
    
    X, y = svm_trainer.prepare_features(df)
    
    # 3 rows total.
    # Code now explicitly drops the last row.
    # Result: 2 rows.
    # And dropna check.
    
    assert len(X) == 2
    assert len(y) == 2
    assert "Feature1" in X.columns
    assert "Close" not in X.columns 

@patch("src.models.train_svm.joblib.dump")
@patch("src.models.train_svm.SVMTrainer.load_data")
@patch("src.models.train_svm.GridSearchCV")
def test_svm_train(mock_grid_search, mock_load_data, mock_joblib_dump, svm_trainer):
     # Mock Data - 50 rows
    df = pd.DataFrame({
        "Close": np.random.rand(50),
        "Open": np.random.rand(50),
        "High": np.random.rand(50),
        "Low": np.random.rand(50),
        "Volume": np.random.rand(50),
        "Ticker": ["AAPL"]*50,
        "date_only": ["2023-01-01"]*50,
        "Feature1": np.random.rand(50)
    })
    mock_load_data.return_value = df
    
    # prepare_features will result in 49 rows (drop last)
    # train_size = 0.8 * 49 = 39.2 -> 39
    # test_size = 49 - 39 = 10
    
    mock_grid = MagicMock()
    mock_grid.best_params_ = {"C": 1}
    # Mock predict to return 10 items to match test set
    mock_grid.predict.return_value = np.zeros(10) 
    mock_grid_search.return_value = mock_grid

    svm_trainer.train("AAPL")
    
    assert mock_grid.fit.called
    assert mock_joblib_dump.called
