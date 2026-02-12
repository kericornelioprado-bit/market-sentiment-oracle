
import pytest
import pandas as pd
import numpy as np
from src.features import technical_indicators

@pytest.fixture
def sample_price_data():
    # Create a simple predictable series
    return pd.Series([100, 102, 104, 103, 105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116])

def test_calculate_rsi(sample_price_data):
    rsi = technical_indicators.calculate_rsi(sample_price_data, period=5)
    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(sample_price_data)
    # Check bounds
    assert rsi.min() >= 0
    assert rsi.max() <= 100
    # First few should be NaN due to period
    assert pd.isna(rsi.iloc[0])

def test_calculate_macd(sample_price_data):
    macd, signal, hist = technical_indicators.calculate_macd(sample_price_data, fast=3, slow=5, signal=2)
    assert isinstance(macd, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(hist, pd.Series)
    assert len(macd) == len(sample_price_data)

def test_calculate_bollinger_bands(sample_price_data):
    upper, middle, lower, width = technical_indicators.calculate_bollinger_bands(sample_price_data, period=5)
    assert isinstance(upper, pd.Series)
    assert len(upper) == len(sample_price_data)
    
    # Logic checks - handle NaNs
    valid_indices = upper.dropna().index
    assert (upper.loc[valid_indices] >= middle.loc[valid_indices]).all()
    assert (middle.loc[valid_indices] >= lower.loc[valid_indices]).all()

def test_calculate_log_returns(sample_price_data):
    log_returns = technical_indicators.calculate_log_returns(sample_price_data)
    expected_first_return = np.log(102) - np.log(100) # log(Pt) - log(Pt-1)
    # Check second element (index 1) which corresponds to the first return
    assert np.isclose(log_returns.iloc[1], expected_first_return)

def test_add_technical_features():
    df = pd.DataFrame({"Close": [100, 101, 102, 103, 104, 105] * 5}) # Enough data for windows
    df_result = technical_indicators.add_technical_features(df)
    
    expected_columns = [
        "log_returns", "rsi_14", "macd_line", "macd_signal", "macd_hist",
        "bb_upper", "bb_lower", "bb_width", "volatility_21d"
    ]
    for col in expected_columns:
        assert col in df_result.columns
