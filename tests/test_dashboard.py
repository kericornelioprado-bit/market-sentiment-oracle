import sys
from unittest.mock import MagicMock, patch
import types

def test_load_model_security():
    """Test load_model security preventing path traversal."""

    # Mock dependencies
    mock_st = MagicMock()
    mock_st.cache_data = lambda func: func
    mock_st.cache_resource = lambda func: func
    # Mock columns to return 4 mocks
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    # Create mocks for other modules
    mock_storage = MagicMock()

    # Configure storage mock
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_storage.Client.return_value = mock_client
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_blob.download_as_bytes.return_value = b"fake_data"
    mock_blob.exists.return_value = True

    # Use ModuleType for pandas to pass type checks
    mock_pd = types.ModuleType("pandas")

    class MockSeries:
        pass

    class MockIndex:
        pass

    class MockDataFrame:
        pass

    mock_pd.Series = MockSeries
    mock_pd.Index = MockIndex
    mock_pd.DataFrame = MockDataFrame

    mock_pd.read_parquet = MagicMock()

    # Configure pandas mock to return a usable dataframe
    mock_df = MagicMock()
    mock_pd.read_parquet.return_value = mock_df

    # Configure df["Col"] to return list (accepted by Plotly)
    def df_getitem(key):
        return [100.0] * 15 # Enough for tail(10) logic
    mock_df.__getitem__.side_effect = df_getitem

    # Configure df.index to be list
    mock_df.index = list(range(15))

    # Configure df columns
    mock_df.columns = ["Open", "High", "Low", "Close", "Volume", "rsi_14", "daily_sentiment", "bb_upper", "bb_lower"]

    # Configure df.iloc to return latest and prev rows with valid numbers
    mock_latest = MagicMock()
    mock_prev = MagicMock()

    def iloc_getitem(arg):
        if arg == -1:
            return mock_latest
        if arg == -2:
            return mock_prev
        return MagicMock()

    mock_df.iloc.__getitem__.side_effect = iloc_getitem

    # Configure __getitem__ for rows to return floats for metrics
    def row_getitem(key):
        if key == "Close":
            return 100.0
        if key == "rsi_14":
            return 50.0
        if key == "daily_sentiment":
            return 0.5
        if key == "bb_upper":
            return 110.0
        if key == "bb_lower":
            return 90.0
        return MagicMock() # For other keys

    mock_latest.__getitem__.side_effect = row_getitem
    mock_prev.__getitem__.side_effect = row_getitem

    # Configure tail() logic
    mock_subset = MagicMock()
    mock_tail = MagicMock()
    mock_subset.tail.return_value = mock_tail
    mock_tail.values = [[1.0]*len(mock_df.columns)] * 10

    def df_getitem_complex(key):
        if isinstance(key, list):
            return mock_subset
        return [100.0] * 15

    mock_df.__getitem__.side_effect = df_getitem_complex

    # Use a simpler patch dict
    modules_to_patch = {
        "streamlit": mock_st,
        "google.cloud.storage": mock_storage,
        "tensorflow": MagicMock(),
        "joblib": MagicMock(),
        "pandas": mock_pd,
    }

    with patch.dict(sys.modules, modules_to_patch):
        # Reload app to apply mocks
        if "src.dashboard.app" in sys.modules:
            del sys.modules["src.dashboard.app"]
        from src.dashboard.app import load_model

        # Patch Path in the app module
        with patch("src.dashboard.app.Path") as MockPath:
            # Setup the base dir
            mock_base = MagicMock()
            mock_base.__str__.return_value = "/safe/models"

            # When Path("models") is called, return a mock that resolves to mock_base
            MockPath.return_value.resolve.return_value = mock_base

            # --- Test Case 1: Valid Path ---
            mock_model_path = MagicMock()
            mock_model_path.resolve.return_value = mock_model_path
            mock_model_path.exists.return_value = True
            mock_model_path.is_relative_to.return_value = True # Valid
            mock_model_path.__str__.return_value = "/safe/models/lstm_AAPL.keras"

            mock_scaler_path = MagicMock()
            mock_scaler_path.resolve.return_value = mock_scaler_path
            mock_scaler_path.exists.return_value = True
            mock_scaler_path.is_relative_to.return_value = True # Valid
            mock_scaler_path.__str__.return_value = "/safe/models/scaler_lstm_AAPL.pkl"

            # Configure joinpath to return the mock paths
            mock_base.joinpath.side_effect = [mock_model_path, mock_scaler_path]

            model, scaler = load_model("AAPL")

            # Assertions
            assert model is not None, "Valid path should return model"
            assert scaler is not None, "Valid path should return scaler"

            # --- Test Case 2: Path Traversal ---
            # Reset mocks
            mock_base.joinpath.side_effect = None

            bad_model_path = MagicMock()
            bad_model_path.resolve.return_value = bad_model_path
            bad_model_path.is_relative_to.return_value = False # INVALID
            # Emulate a resolved path outside the base directory
            bad_model_path.__str__.return_value = "/etc/passwd"

            bad_scaler_path = MagicMock()
            bad_scaler_path.resolve.return_value = bad_scaler_path
            bad_scaler_path.is_relative_to.return_value = False # INVALID
            bad_scaler_path.__str__.return_value = "/safe/models/scaler.pkl"

            def joinpath_side_effect(arg):
                if "lstm_" in arg:
                    return bad_model_path
                return bad_scaler_path

            mock_base.joinpath.side_effect = joinpath_side_effect

            model, scaler = load_model("../../../etc/passwd")

            # Should return None, None due to validation failure
            assert model is None, "Path traversal should return None"
            assert scaler is None, "Path traversal should return None"
