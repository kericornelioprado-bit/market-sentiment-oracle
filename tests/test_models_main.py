
import pytest
from unittest.mock import patch
from src.models import train_lstm, train_svm

# Add tests for main execution logic (simulated by calling functions that would be called in main)

# train_lstm.py main just calls trainer.train() for tickers
@patch("src.models.train_lstm.LSTMTrainer.train")
@patch("src.models.train_lstm.storage.Client")
def test_lstm_main_logic(mock_client, mock_train):
    # Call the actual main function
    train_lstm.main()
    assert mock_train.called

# train_svm.py main just calls trainer.train() for tickers
@patch("src.models.train_svm.SVMTrainer.train")
@patch("src.models.train_svm.storage.Client")
def test_svm_main_logic(mock_client, mock_train):
    train_svm.main()
    assert mock_train.called
