# Estrategia de Pruebas

Este documento describe la metodología de testing utilizada para asegurar la calidad y robustez del código en `market-sentiment-oracle`.

## 🛠️ Stack Tecnológico

* **Runner**: `pytest` (gestionado vía `uv`).
* **Generación de Tests**: `Gemini CLI` (AI-Driven Test Generation).
* **Mocking**: `pytest-mock` para aislar dependencias externas (NewsAPI, GCS).
* **Validación de Datos**: `pandera` para asegurar contratos de datos.

## 🧪 Cobertura de Pruebas

Las pruebas se encuentran en el directorio `tests/` y cubren los siguientes aspectos críticos:

### 1. Ingesta de Datos (`test_ingest.py`, `test_market_data_ingest.py`)

Se verifican los módulos de extracción de noticias y datos de mercado.

* **Datos de Mercado (`test_market_data_ingest.py`)**:
    * Validación de `src.data.ingest` usando `unittest.mock` para simular `yfinance`.
    * Asegura que el DataFrame descargado cumpla con el esquema esperado (Open, High, Low, Close, Volume).
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

### 4. Feature Engineering (`test_features.py`, `test_technical_features_integration.py`)

Validación de la generación de indicadores técnicos y fusión de datos.

* **Cálculo de Indicadores**:
    * Verificación de fórmulas para RSI, MACD y Bollinger Bands contra valores esperados.
* **Integración de Indicadores (`test_technical_features_integration.py`)**:
    * Pruebas de integración para asegurar que `add_technical_features` genera correctamente todas las columnas requeridas sin errores de ejecución.
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

## 🚀 Ejecución de Pruebas

Para ejecutar la suite de pruebas localmente:

```bash
# Sincronizar entorno
uv sync

# Ejecutar pytest
uv run pytest
```

## 📊 Resumen de Ejecución (2026-02-08)

| Módulo | Archivo | Tests Activos |
| :--- | :--- | :--- |
| Ingesta (Noticias) | `tests/test_ingest.py` | 9 |
| Ingesta (Mercado) | `tests/test_market_data_ingest.py` | 3 |
| Procesamiento | `tests/test_process_sentiment.py` | 5 |
| Features | `tests/test_features.py` | 3 |
| Features (Integración) | `tests/test_technical_features_integration.py` | 1 |
| Modelos | `tests/test_models.py` | 5 |
| Backtesting | `tests/test_backtest.py` | 3 |
| Dashboard | `tests/test_dashboard.py` | 1 |
| Integración | `tests/test_integration.py` | 1 |
| **Total** | | **31** |
