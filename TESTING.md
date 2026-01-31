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

### 4. Feature Engineering (`test_features.py`)

Validación de la generación de indicadores técnicos y fusión de datos.

* **Cálculo de Indicadores**:
    * Verificación de fórmulas para RSI, MACD y Bollinger Bands contra valores esperados.
* **Integridad de Datos**:
    * Asegurar que no se introduzcan NaNs inesperados y que el índice de fechas se mantenga consistente.

### 5. Modelos (`test_models.py`)

Pruebas para el entrenamiento y persistencia de modelos (LSTM, SVM).

* **Entrenamiento**:
    * Verificación de que el flujo de entrenamiento (`train`) se ejecuta sin errores con datos simulados.
* **Persistencia**:
    * Comprobación de que los modelos (`.keras`, `.pkl`) se guardan correctamente en el disco.

### 6. Backtesting (`test_backtest.py`)

Verificación de la lógica de simulación de estrategias.

* **Ejecución de Estrategia**:
    * Validación del cálculo de PnL (Profit and Loss) y métricas de desempeño (Sharpe Ratio).

### 7. Dashboard (`test_dashboard.py`)

Pruebas de la interfaz de usuario (Streamlit) y visualización.

* **Carga de Componentes**:
    * Verificación de que los componentes principales del dashboard se renderizan sin excepciones.

### 8. Ingesta de Datos de Mercado (Raw) (`test_market_data_ingest.py`)

Validación de la descarga de datos históricos desde Yahoo Finance.

* **Mocking de API Externa**:
    * Uso de `unittest.mock.patch` para interceptar llamadas a `yfinance.download`.
    * Simulación de DataFrames vacíos y manejo de excepciones de red.
* **Persistencia**:
    * Verificación de llamadas a `to_parquet` y creación de directorios.

## 🚀 Ejecución de Pruebas

Para ejecutar la suite de pruebas localmente:

```bash
# Sincronizar entorno
uv sync

# Ejecutar pytest
uv run pytest
