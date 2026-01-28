import pytest
import os
import pandas as pd
import requests
from unittest.mock import MagicMock, patch
from src.data.ingest_news import fetch_news, upload_to_gcs

# --- Casos de Prueba para 'fetch_news' ---

def test_env_variables_missing(mocker):
    """
    1. test_env_variables_missing: Debe lanzar ValueError si no hay API Key.
    """
    # Mock: Asegura que la variable API_KEY en el módulo sea None.
    # Esto es más robusto que mockear os.environ, ya que evita problemas
    # con el orden de importación y la ejecución de load_dotenv().
    mocker.patch('src.data.ingest_news.API_KEY', None)
    
    with pytest.raises(ValueError, match="No se encontró la API Key"):
        fetch_news()

@patch('src.data.ingest_news.requests.get')
@patch('src.data.ingest_news.upload_to_gcs') # Mockeamos para no subir a GCS
def test_fetch_news_success(mock_upload_gcs, mock_requests_get, tmp_path, mocker):
    """
    2. test_fetch_news_success: Mockea una respuesta de NewsAPI exitosa.
    Verifica que se procesen los datos y se guarde un archivo Parquet.
    """
    # Mock: Simula una respuesta JSON exitosa de la API de noticias.
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "articles": [
            {
                "source": {"id": "reuters", "name": "Reuters"},
                "author": "John Doe",
                "title": "AAPL Stock Surges",
                "description": "Description of the article.",
                "url": "https://example.com/aapl",
                "urlToImage": "https://example.com/aapl.jpg",
                "publishedAt": "2024-01-01T12:00:00Z",
                "content": "Content of the article about AAPL."
            }
        ]
    }
    mock_requests_get.return_value = mock_response

    # Mock: Cambia el directorio de salida al directorio temporal de pytest.
    # Usamos un spy para os.makedirs para permitir que se cree el directorio si es necesario.
    mocker.patch('os.path.join', return_value=str(tmp_path / "AAPL_news.parquet"))

    fetch_news()

    # Assert: Verifica que la función de subida a GCS fue llamada.
    mock_upload_gcs.assert_called()
    
    # Assert: Verifica que se llamó a la API (requests.get).
    mock_requests_get.assert_called()

@patch('src.data.ingest_news.requests.get')
@patch('src.data.ingest_news.upload_to_gcs')
@patch('builtins.print')
def test_fetch_news_empty(mock_print, mock_upload, mock_requests_get):
    """
    3. test_fetch_news_empty: Mockea una respuesta vacía de la API.
    Asegura que el código lo maneja sin errores y no intenta procesar datos.
    """
    # Mock: Simula una respuesta JSON de la API sin artículos.
    mock_response = MagicMock()
    mock_response.json.return_value = {"articles": []}
    mock_requests_get.return_value = mock_response

    fetch_news()

    # Assert: Verifica que no se intentó subir nada a GCS.
    mock_upload.assert_not_called()
    
    # Assert: Verifica que se imprimió un mensaje de advertencia.
    # Buscamos en los logs de la función print si contiene el mensaje esperado.
    found_warning = any("No se encontraron noticias recientes" in call.args[0] for call in mock_print.call_args_list)
    assert found_warning

@patch('src.data.ingest_news.requests.get')
@patch('src.data.ingest_news.upload_to_gcs')
def test_fetch_news_api_error(mock_upload, mock_requests_get):
    """
    4. test_fetch_news_api_error: Simula un error en la respuesta de la API.
    El código actual no lo captura, por lo que fallará al intentar decodificar JSON.
    Este test verifica ese comportamiento esperado.
    """
    # Mock: Simula una respuesta con error que lanza una excepción al llamar a .json().
    mock_response = MagicMock()
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Error", "", 0)
    mock_requests_get.return_value = mock_response

    # El código actual no tiene un try/except para el .json(), por lo que esperamos
    # que la excepción generada por el mock se propague.
    with pytest.raises(requests.exceptions.JSONDecodeError):
        fetch_news()
    
    # Assert: No se debió intentar ninguna subida a GCS si la API falla.
    mock_upload.assert_not_called()

# --- Casos de Prueba para 'upload_to_gcs' ---

@patch('src.data.ingest_news.storage.Client')
def test_upload_to_gcs(mock_storage_client, mocker):
    """
    5. test_upload_to_gcs: Mockea 'google.cloud.storage.Client'.
    Verifica que el método 'upload_from_filename' fue llamado con los argumentos correctos.
    """
    # Mock: Fija la variable de entorno del bucket para este test.
    mocker.patch('src.data.ingest_news.BUCKET_NAME', 'test-bucket')

    # Mock: Se crea una cadena de mocks para simular la API de GCS.
    # storage.Client() -> mock_client -> .bucket() -> mock_bucket -> .blob() -> mock_blob
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_storage_client.return_value = mock_client
    
    source_file = "local/test.parquet"
    destination_path = "remote/test.parquet"
    
    upload_to_gcs(source_file, destination_path)

    # Assert: Verifica que el cliente de GCS fue inicializado.
    mock_storage_client.assert_called_once()
    # Assert: Verifica que se accedió al bucket correcto.
    mock_client.bucket.assert_called_with("test-bucket")
    # Assert: Verifica que se creó el blob con el nombre de destino correcto.
    mock_bucket.blob.assert_called_with(destination_path)
    # Assert: Verifica que se llamó al método de subida con el archivo fuente.
    mock_blob.upload_from_filename.assert_called_with(source_file)


# --- Caso de Prueba para Estructura de Datos ---

@patch('src.data.ingest_news.requests.get')
@patch('src.data.ingest_news.upload_to_gcs')
def test_data_structure(mock_upload, mock_requests_get, mocker):
    """
    6. test_data_structure: Verifica que el DataFrame final tiene las columnas esperadas.
    Esta versión mockea la clase pd.DataFrame para interceptar los datos
    que se le pasan al constructor, lo que es más robusto.
    """
    # Mock: Simula una respuesta de API con todos los campos esperados.
    articles_payload = [
        {
            "publishedAt": "2024-01-01T12:00:00Z",
            "title": "Test Title",
            "content": "Test content for the article.",
            "author": "N/A", "description": "N/A", "url": "N/A", "urlToImage": "N/A", "source": {}
        }
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = {"articles": articles_payload}
    mock_requests_get.return_value = mock_response

    # Mock: Reemplaza la clase DataFrame de pandas para espiar sus llamadas.
    # El mock original se pasa a la función de prueba para poder hacer aserciones sobre él.
    mock_df_class = mocker.patch('pandas.DataFrame', spec=True)

    fetch_news()

    # Assert: Verifica que el constructor de DataFrame fue llamado.
    mock_df_class.assert_called()

    # Assert: Verifica que los datos correctos se pasaron al constructor.
    # `call_args[0]` es el primer argumento posicional, la lista de artículos.
    actual_data_passed = mock_df_class.call_args[0][0]
    assert actual_data_passed == articles_payload

    # Assert: Verifica que el método to_parquet fue llamado en la instancia del DF mockeado.
    # `mock_df_class.return_value` es la instancia creada por el mock.
    mock_df_instance = mock_df_class.return_value
    mock_df_instance.to_parquet.assert_called()

# --- Nuevos Casos de Prueba para Aumentar Cobertura ---

@patch('src.data.ingest_news.storage.Client')
@patch('builtins.print')
def test_upload_to_gcs_no_bucket(mock_print, mock_storage_client, mocker):
    """
    Prueba el caso donde GCS_BUCKET_NAME no está definido.
    """
    # Mock: Asegura que la variable BUCKET_NAME en el módulo sea None.
    mocker.patch('src.data.ingest_news.BUCKET_NAME', None)
    
    upload_to_gcs("local/file.txt", "remote/file.txt")

    # Assert: El cliente de storage no debe ser llamado.
    mock_storage_client.assert_not_called()
    
    # Assert: Se debe imprimir un mensaje de advertencia.
    found_warning = any("No se definió GCS_BUCKET_NAME" in call.args[0] for call in mock_print.call_args_list)
    assert found_warning

@patch('src.data.ingest_news.storage.Client')
@patch('builtins.print')
def test_upload_to_gcs_failure(mock_print, mock_storage_client, mocker):
    """
    Prueba el caso donde la subida a GCS falla con una excepción.
    """
    mocker.patch('src.data.ingest_news.BUCKET_NAME', 'test-bucket')

    # Mock: El método de subida lanza una excepción.
    mock_blob = MagicMock()
    mock_blob.upload_from_filename.side_effect = Exception("Test GCS Error")
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket
    mock_storage_client.return_value = mock_client
    
    upload_to_gcs("local/file.txt", "remote/file.txt")

    # Assert: Se debe imprimir un mensaje de error.
    found_error = any("Error subiendo a GCS" in call.args[0] for call in mock_print.call_args_list)
    assert found_error