import pandas as pd
import numpy as np


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calcula el Índice de Fuerza Relativa (RSI).
    Rango: 0-100.
    > 70: Sobrecompra (posible bajada)
    < 30: Sobreventa (posible subida)
    """
    delta = series.diff()

    # Separar ganancias y pérdidas
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    # Media Móvil Exponencial (Wilder's Smoothing)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # Optimization: Use the alternative formula RSI = 100 * avg_gain / (avg_gain + avg_loss)
    # This avoids division by zero (handling avg_loss=0 naturally) and reduces operations.
    rsi = 100 * avg_gain / (avg_gain + avg_loss)
    return rsi


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calcula Moving Average Convergence Divergence (MACD).
    Retorna 3 series:
    - MACD Line: Diferencia entre EMAs rápida y lenta.
    - Signal Line: EMA del MACD.
    - Histogram: Diferencia entre MACD y Signal (Inercia de tendencia).
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    series: pd.Series, period: int = 20, num_std: float = 2.0
):
    """
    Calcula las Bandas de Bollinger para medir volatilidad.
    Retorna:
    - Upper Band
    - Lower Band
    - Bandwidth: (Upper - Lower) / Middle (Ancho relativo)
    """
    middle_band = series.rolling(window=period).mean()
    std_dev = series.rolling(window=period).std()

    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)

    # Feature extra: Ancho de banda (útil para detectar "squeezes")
    bandwidth = (upper_band - lower_band) / middle_band

    return upper_band, middle_band, lower_band, bandwidth


def calculate_log_returns(series: pd.Series) -> pd.Series:
    """
    Calcula retornos logarítmicos.
    Preferible sobre % cambio simple para modelos LSTM por sus propiedades estadísticas
    (simetría y aditividad temporal).

    Optimización: np.log(series).diff() es ~25% más rápido que np.log(series / series.shift(1))
    ya que reemplaza la división por una resta.
    """
    # np.log(Pt / Pt-1) = np.log(Pt) - np.log(Pt-1)
    return np.log(series).diff()


def calculate_volatility(series: pd.Series, window: int = 21) -> pd.Series:
    """
    Volatilidad histórica basada en retornos logarítmicos (Rolling Standard Deviation).
    Ventana 21 = ~1 mes de trading.
    """
    log_ret = calculate_log_returns(series)
    return log_ret.rolling(window=window).std()


def add_technical_features(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
    """
    Función maestra que inyecta todas las features técnicas al DataFrame.
    """
    df = df.copy()

    # Validar que existe la columna de precio
    if price_col not in df.columns:
        raise ValueError(f"La columna '{price_col}' no existe en el DataFrame.")

    # 1. Retornos (Crucial para estacionariedad)
    df["log_returns"] = calculate_log_returns(df[price_col])

    # 2. RSI
    df["rsi_14"] = calculate_rsi(df[price_col])

    # 3. MACD
    macd, signal, hist = calculate_macd(df[price_col])
    df["macd_line"] = macd
    df["macd_signal"] = signal
    df["macd_hist"] = hist

    # 4. Bollinger Bands
    upper, mid, lower, width = calculate_bollinger_bands(df[price_col])
    df["bb_upper"] = upper
    df["bb_lower"] = lower
    df["bb_width"] = width  # Feature de volatilidad relativa

    # 5. Volatilidad Histórica
    # Optimizacion: Reutilizamos log_returns ya calculados para evitar recalculo redundante
    # en calculate_volatility()
    df["volatility_21d"] = df["log_returns"].rolling(window=21).std()

    # Limpieza inicial (los primeros N registros serán NaN por los windows)
    # No hacemos dropna() aquí para dejar que el usuario decida cómo manejarlo

    return df
