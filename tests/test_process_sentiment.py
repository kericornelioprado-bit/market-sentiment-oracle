from unittest.mock import MagicMock
import torch
from src.process_sentiment import get_sentiment_batch

def test_get_sentiment_batch_logic():
    # Mock tokenizer
    mock_tokenizer = MagicMock()
    # When called, return some dict mimicking inputs
    # Need to return objects that have .to() method
    mock_tensor = MagicMock()
    mock_tensor.to.return_value = mock_tensor # Chainable

    mock_tokenizer.return_value = {"input_ids": mock_tensor, "attention_mask": mock_tensor}

    # Mock model
    mock_model = MagicMock()
    # Mock output logits
    # Let's say batch size 2.
    # Item 1: Positive (index 0 is max)
    # Item 2: Negative (index 1 is max)
    # Logits shape: [batch, 3]
    logits = torch.tensor([
        [10.0, 0.0, 0.0], # Strong positive
        [0.0, 10.0, 0.0]  # Strong negative
    ])
    mock_model.return_value.logits = logits
    # Mock device attribute
    mock_model.device = 'cpu'

    texts = ["Good news", "Bad news"]
    results = get_sentiment_batch(texts, mock_tokenizer, mock_model, batch_size=2)

    assert len(results) == 2
    assert results[0][0] == "positive"
    assert results[1][0] == "negative"
    # Scores should be close to 1.0 due to softmax on 10,0,0
    assert results[0][1] > 0.99
    assert results[1][1] > 0.99

def test_get_sentiment_batch_empty_handling():
    mock_tokenizer = MagicMock()
    mock_tensor = MagicMock()
    mock_tensor.to.return_value = mock_tensor
    mock_tokenizer.return_value = {"input_ids": mock_tensor}

    mock_model = MagicMock()
    mock_model.device = 'cpu'

    # Only one valid text, so logits should be size [1, 3]
    logits = torch.tensor([
        [0.0, 0.0, 10.0] # Neutral
    ])
    mock_model.return_value.logits = logits

    texts = ["", "Valid text", "   "]
    results = get_sentiment_batch(texts, mock_tokenizer, mock_model, batch_size=3)

    assert len(results) == 3
    # Empty -> Neutral, 0.0
    assert results[0] == ("neutral", 0.0)
    assert results[2] == ("neutral", 0.0)

    # Valid -> Neutral (from mock)
    assert results[1][0] == "neutral"
    assert results[1][1] > 0.99

    # Verify tokenizer was called ONLY with "Valid text"
    # Args[0] of the call
    called_texts = mock_tokenizer.call_args[0][0]
    assert called_texts == ["Valid text"]
