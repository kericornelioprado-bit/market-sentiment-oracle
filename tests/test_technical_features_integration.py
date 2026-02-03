import pandas as pd
import numpy as np
from src.features.technical_indicators import (
    add_technical_features,
    calculate_log_returns,
    calculate_volatility,
)


def test_add_technical_features_structure():
    # Create 30 days of data to satisfy 21d window
    prices = np.random.randn(50) + 100
    dates = pd.date_range(start="2024-01-01", periods=50)
    df = pd.DataFrame({"Close": prices}, index=dates)

    df_features = add_technical_features(df, price_col="Close")

    expected_columns = [
        "log_returns",
        "rsi_14",
        "macd_line",
        "macd_signal",
        "macd_hist",
        "bb_upper",
        "bb_lower",
        "bb_width",
        "volatility_21d",
    ]

    for col in expected_columns:
        assert col in df_features.columns

    # Verify volatility calculation matches the manual call (to ensure optimization didn't break logic)
    # Note: Manual call recalculates log returns internally using the NEW optimized calculate_log_returns
    # so results should match exactly.
    manual_vol = calculate_volatility(df["Close"])
    pd.testing.assert_series_equal(
        df_features["volatility_21d"],
        manual_vol,
        obj="Volatility Series",
        check_names=False,
    )

    # Verify log returns match manual calculation
    manual_log_ret = calculate_log_returns(df["Close"])
    pd.testing.assert_series_equal(
        df_features["log_returns"],
        manual_log_ret,
        obj="Log Returns Series",
        check_names=False,
    )
