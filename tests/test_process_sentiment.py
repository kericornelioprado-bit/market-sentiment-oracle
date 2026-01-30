from unittest.mock import MagicMock, patch
import torch
import pandas as pd
import io

from src.process_sentiment import get_sentiment_batch, process_bucket_files

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

from src.process_sentiment import get_sentiment

def test_get_sentiment_logic():
    """
    Test the core logic of get_sentiment function with mocked tokenizer and model.
    """
    # Mock tokenizer
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "attention_mask": torch.tensor([[1, 1, 1]])
    }

    # Mock model
    mock_model = MagicMock()
    # Simulate a strong positive prediction: index 0 (positive) is max
    mock_model.return_value.logits = torch.tensor([[10.0, 0.0, 0.0]])

    # Call the function under test
    label, score = get_sentiment("Test news for positive sentiment", mock_tokenizer, mock_model)

    # Assertions
    assert label == "positive"
    # Verify score is close to 1.0 after softmax of [10.0, 0.0, 0.0]
    assert score > 0.99

def test_get_sentiment_empty_text():
    """
    Test get_sentiment with empty or whitespace-only text.
    """
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()

    label, score = get_sentiment("", mock_tokenizer, mock_model)
    assert label == "neutral"
    assert score == 0.0

    label, score = get_sentiment("   ", mock_tokenizer, mock_model)
    assert label == "neutral"
    assert score == 0.0

    label, score = get_sentiment(None, mock_tokenizer, mock_model)
    assert label == "neutral"
    assert score == 0.0


@patch('src.process_sentiment.storage.Client')
@patch('src.process_sentiment.AutoTokenizer.from_pretrained')
@patch('src.process_sentiment.AutoModelForSequenceClassification.from_pretrained')
def test_process_end_to_end(mock_model_loader, mock_tokenizer_loader, mock_gcs_client):
    """
    Test a full run of the bucket processing logic with mocked external services.
    """
    # --- 1. Setup Mocks ---

    # a) GCS Client and Bucket
    mock_blob_content = pd.DataFrame({'title': ['Positive news', 'Negative news']}).to_parquet()

    mock_blob = MagicMock()
    mock_blob.name = "data/raw/news_2024-01-01.parquet"
    mock_blob.download_as_bytes.return_value = mock_blob_content
    
    mock_bucket = MagicMock()
    mock_bucket.list_blobs.return_value = [mock_blob]
    # Create a mock for the blob that will be uploaded
    mock_new_blob = MagicMock()
    mock_bucket.blob.return_value = mock_new_blob
    
    mock_gcs_client.return_value.bucket.return_value = mock_bucket

    # b) Transformers Model and Tokenizer
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": torch.zeros(1, 1), "attention_mask": torch.zeros(1, 1)}
    mock_tokenizer_loader.return_value = mock_tokenizer
    
    mock_model = MagicMock()
    # Mock return value for a batch of 2: [positive, negative]
    logits = torch.tensor([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0]])
    mock_model.return_value.logits = logits
    mock_model.device = 'cpu'
    mock_model_loader.return_value = mock_model

    # --- 2. Run the function ---
    process_bucket_files()

    # --- 3. Assertions ---

    # Verify GCS client was called
    mock_gcs_client.assert_called_once()
    mock_gcs_client.return_value.bucket.assert_called_once_with("market-oracle-tesis-data-lake")

    # Verify model loading
    mock_tokenizer_loader.assert_called_once_with("ProsusAI/finbert")
    mock_model_loader.assert_called_once_with("ProsusAI/finbert")

    # Verify file listing and download
    mock_bucket.list_blobs.assert_called_once_with(prefix="data/raw/")
    mock_blob.download_as_bytes.assert_called_once()
    
    # Verify new blob was created for upload
    expected_new_blob_name = "data/processed/embeddings/news_2024-01-01.parquet"
    mock_bucket.blob.assert_called_once_with(expected_new_blob_name)
    
    # Verify the upload happened
    mock_new_blob.upload_from_file.assert_called_once()
    
    # Verify content of the upload
    # Get the BytesIO object passed to the upload function
    upload_args = mock_new_blob.upload_from_file.call_args[0]
    output_buffer = upload_args[0]
    output_buffer.seek(0)
    
    # Read the parquet data from the buffer and verify its contents
    df_uploaded = pd.read_parquet(output_buffer)
    
    assert 'sentiment_label' in df_uploaded.columns
    assert 'sentiment_score' in df_uploaded.columns
    assert df_uploaded.loc[0, 'sentiment_label'] == 'positive'
    assert df_uploaded.loc[1, 'sentiment_label'] == 'negative'
    assert df_uploaded.loc[0, 'sentiment_score'] > 0.99
    assert df_uploaded.loc[1, 'sentiment_score'] > 0.99