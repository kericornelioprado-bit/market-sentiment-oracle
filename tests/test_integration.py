import pytest
from unittest.mock import patch, MagicMock
from src.data.ingest_news import fetch_news


@pytest.mark.integration
@patch("src.data.ingest_news.storage.Client")
@patch("src.data.ingest_news.requests.get")
def test_pipeline_end_to_end_local(
    mock_requests_get, mock_gcs_client, tmp_path, mocker
):
    """
    Prueba de integración del flujo completo.
    """
    # 1. Configuración de Mocks
    valid_article_data = {
        "articles": [
            {
                "publishedAt": "2024-01-27T10:00:00Z",
                "title": "Integration Test: Stocks Soar",
                "url": "https://example.com/test-article",
                "content": "Content",
                "source": {"id": "test", "name": "Test"},  # Esto será filtrado
                "author": "Bot",  # Esto también
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = valid_article_data
    mock_requests_get.return_value = mock_response

    # Redirigir guardado de archivos a carpeta temporal del test
    temp_file_path = tmp_path / "AAPL_news.parquet"
    mocker.patch("os.path.join", return_value=str(temp_file_path))

    # Variables de entorno falsas
    mocker.patch("src.data.ingest_news.API_KEY", "fake-key")
    mocker.patch("src.data.ingest_news.BUCKET_NAME", "fake-bucket")

    # 2. Ejecución
    # IMPORTANTE: Pasamos solo 1 símbolo para probar el ciclo una sola vez
    fetch_news(symbols=["AAPL"])

    # 3. Verificación
    # Como solo pasamos AAPL, debe llamarse 1 vez.
    mock_gcs_client.return_value.bucket.return_value.blob.return_value.upload_from_filename.assert_called_once()
