# Estrategia de Pruebas

Este documento describe la metodología de testing utilizada para asegurar la calidad y robustez del código en `market-sentiment-oracle`.

## 🛠️ Stack Tecnológico

* **Runner**: `pytest` (gestionado vía `uv`).
* **Generación de Tests**: `Gemini CLI` (AI-Driven Test Generation).
* **Mocking**: `pytest-mock` para aislar dependencias externas (NewsAPI, GCS).
* **Validación de Datos**: `pandera` para asegurar contratos de datos.

## 🧪 Cobertura de Pruebas

Las pruebas se encuentran en el directorio `tests/` y cubren los siguientes aspectos críticos:

### 1. Ingesta de Datos (`test_ingest.py`)

Se verifica el módulo `src.data.ingest_news` para asegurar la robustez de la extracción.

* **Gestión de Estado (Patrón Singleton)**:
    * Uso de `pytest.fixture(autouse=True)` para reiniciar el cliente global de GCS entre pruebas, evitando contaminación de estado (`reset_global_client`).
* **Interacción con API Externa**:
    * Simulación (Mock) de respuestas de NewsAPI y manejo de JSONs inválidos.
* **Validación de Esquema**:
    * Cumplimiento estricto de `NewsArticleSchema` (Pandera).
* **Interacción con la Nube (GCS)**:
    * Verificación de llamadas a `upload_from_filename` sin conexión real a internet.

### 2. Procesamiento de Sentimiento (`test_process_sentiment.py`)

Se verifican las optimizaciones de inferencia en `src.process_sentiment`.

* **Lógica de Batching**:
    * Validación de `get_sentiment_batch` para asegurar que los resultados correspondan a los inputs en el orden correcto.
* **Manejo de Casos Borde**:
    * Verificación del comportamiento ante textos vacíos o nulos (retorno de "neutral").

### 3. Pruebas de Integración (`test_integration.py`)

Pruebas end-to-end simuladas para validar el flujo completo.

* **Pipeline de Ingesta**:
    * Ejecución de `fetch_news` con mocks de `requests` y `google.cloud.storage`.
    * Verificación de la creación de archivos Parquet y llamadas de subida a GCS.

## 🚀 Ejecución de Pruebas

Para ejecutar la suite de pruebas localmente:

```bash
# Sincronizar entorno
uv sync

# Ejecutar pytest
uv run pytest
