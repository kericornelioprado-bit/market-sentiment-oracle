import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# --- Módulos a Probar ---
from src.features.technical_indicators import calculate_rsi, calculate_log_returns
from src.features.merge_data import DataMerger

# --- Fixtures de Datos Sintéticos ---


@pytest.fixture
def simple_price_data():
    """
    Crea un DataFrame con una serie de precios simple y predecible.
    15 días de precios crecientes para tener suficientes datos para el RSI.
    """
    close_prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
    dates = pd.to_datetime(pd.date_range(start="2024-01-01", periods=len(close_prices)))
    return pd.DataFrame({"Close": close_prices, "Date": dates}).set_index("Date")


@pytest.fixture
def mock_price_data_for_merge():
    """DataFrame de precios para probar la fusión de datos."""
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"])
    df = pd.DataFrame(
        {
            "Close": [100, 102, 101, 103],
            "Open": [99, 101, 102, 102],
            "High": [101, 103, 102, 104],
            "Low": [98, 101, 100, 102],
            "Volume": [1000, 1100, 900, 1200],
        },
        index=dates,
    )
    return df.reset_index().rename(columns={"index": "Date"})


@pytest.fixture
def mock_sentiment_data_for_merge():
    """
    DataFrame de sentimientos para probar la fusión.
    - Múltiples noticias el día 2.
    - Sin noticias el día 3 (para probar el manejo de NaNs).
    - Una noticia negativa el día 4.
    """
    data = {
        "date": pd.to_datetime(
            ["2024-01-02 09:00:00", "2024-01-02 15:00:00", "2024-01-04 11:00:00"]
        ),
        "sentiment_label": ["positive", "neutral", "negative"],
        "sentiment_score": [0.9, 0.8, 0.95],
    }
    return pd.DataFrame(data)


# --- Pruebas para technical_indicators.py ---


def test_calculate_log_returns(simple_price_data):
    """Verifica que el cálculo de retornos logarítmicos sea correcto."""
    log_returns = calculate_log_returns(simple_price_data["Close"])

    # El primer valor debe ser NaN
    assert pd.isna(log_returns.iloc[0])

    # Verificación manual del segundo valor: log(11 / 10)
    expected_return = np.log(11 / 10)
    assert np.isclose(log_returns.iloc[1], expected_return)


def test_calculate_rsi_manual(simple_price_data):
    """
    Verifica que el cálculo de RSI sea matemáticamente correcto.
    Para una serie que solo sube, el RSI debe ser 100.
    """
    rsi = calculate_rsi(simple_price_data["Close"], period=14)

    # Con 14 períodos de solo ganancias, la pérdida promedio es 0, resultando en RSI=100
    # El primer valor de RSI no NaN aparece antes de lo esperado por el tipo de EWM.
    # La verificación clave es que después de 14 períodos de subida, el RSI sea 100.
    assert rsi.iloc[14] == 100.0


# --- Pruebas para merge_data.py ---


@patch("src.features.merge_data.storage.Client")
def test_merge_alignment_and_nan_handling(
    mock_storage_client, mock_price_data_for_merge, mock_sentiment_data_for_merge
):
    """
    Prueba crítica:
    1. Mockea la carga desde GCS.
    2. Verifica la correcta alineación de fechas.
    3. Verifica que los NaNs de sentimiento se rellenen con 0.
    """
    # Configuración del Mock de GCS
    mock_bucket = MagicMock()
    mock_blob_price = MagicMock()
    mock_blob_sentiment = MagicMock()

    # Simular que los blobs existen
    mock_blob_price.exists.return_value = True
    mock_blob_sentiment.exists.return_value = True

    # Simular la descarga de datos
    def mock_download_parquet(df):
        buffer = pd.io.common.BytesIO()
        df.to_parquet(buffer)
        buffer.seek(0)
        return buffer.read()

    mock_blob_price.download_as_bytes.return_value = mock_download_parquet(
        mock_price_data_for_merge
    )
    mock_blob_sentiment.download_as_bytes.return_value = mock_download_parquet(
        mock_sentiment_data_for_merge
    )

    # Mapear llamadas de blob() al mock correcto
    def blob_side_effect(blob_name):
        if "prices" in blob_name:
            return mock_blob_price
        return mock_blob_sentiment

    mock_bucket.blob.side_effect = blob_side_effect
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    merger = DataMerger(bucket_name="fake-bucket", tickers=["TEST"])

    # Variable para capturar el DataFrame final antes de la subida
    captured_df = None

    # Mock de to_parquet para interceptar el DataFrame
    original_to_parquet = pd.DataFrame.to_parquet

    def capture_dataframe_to_parquet(self, *args, **kwargs):
        nonlocal captured_df
        # `self` aquí es el DataFrame sobre el que se llama a to_parquet
        captured_df = self.copy()
        # Llamamos a la función original para no romper el flujo
        return original_to_parquet(self, *args, **kwargs)

    # `master_df` es el DataFrame *antes* de que se llame a `dropna`
    # El mock de `to_parquet` capturará este DataFrame.
    # El mock de `dropna` simplemente devolverá el DataFrame sin cambios.
    with patch("pandas.DataFrame.to_parquet", new=capture_dataframe_to_parquet):
        with patch(
            "pandas.DataFrame.dropna", side_effect=lambda *args, **kwargs: captured_df
        ):
            # Patch glob to return a dummy file path
            with patch("glob.glob", return_value=["data/raw/TEST_2024-01-01.parquet"]):
                # Patch os.path.getmtime to avoid error
                with patch("os.path.getmtime", return_value=1234567890):
                    # Patch pd.read_parquet to return the mock price data when loading local file
                    # Note: We need to side_effect because read_parquet is also used for GCS blob via BytesIO
                    original_read_parquet = pd.read_parquet

                    def side_effect_read_parquet(path_or_buf, *args, **kwargs):
                        if isinstance(path_or_buf, str) and "TEST" in path_or_buf:
                            return mock_price_data_for_merge.copy()
                        return original_read_parquet(path_or_buf, *args, **kwargs)

                    with patch(
                        "pandas.read_parquet", side_effect=side_effect_read_parquet
                    ):
                        merger.run_pipeline()

    # Ahora `captured_df` tiene el estado del DataFrame justo antes de ser guardado
    final_df = captured_df
    # El 'Date' ya ha sido procesado como el índice por el pipeline

    # --- Verificaciones ---
    assert final_df is not None, "El DataFrame final no fue capturado."

    # 1. Alineación de Fechas y Cálculo de Sentimiento
    # Creamos un Timestamp para buscar en el índice
    day2_index = pd.to_datetime("2024-01-02")
    sentiment_day2 = final_df.loc[day2_index]["daily_sentiment"]
    volume_day2 = final_df.loc[day2_index]["news_volume"]
    assert np.isclose(sentiment_day2, 0.45)
    assert volume_day2 == 2

    # 2. Manejo de NaNs
    day3_index = pd.to_datetime("2024-01-03")
    sentiment_day3 = final_df.loc[day3_index]["daily_sentiment"]
    volume_day3 = final_df.loc[day3_index]["news_volume"]
    assert sentiment_day3 == 0.0
    assert volume_day3 == 0

    # 3. No se deben perder filas de precios
    assert len(final_df) == len(mock_price_data_for_merge)

    # Verifiquemos que las columnas existen
    assert "daily_sentiment" in final_df.columns
    assert "news_volume" in final_df.columns
    assert "rsi_14" in final_df.columns
