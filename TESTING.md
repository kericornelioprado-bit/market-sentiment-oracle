# Estrategia de Pruebas

Este documento describe la metodología de testing utilizada para asegurar la calidad y robustez del código en `market-sentiment-oracle`.

## 🛠️ Stack Tecnológico

*   **Runner**: `pytest`
*   **Mocking**: `unittest.mock` y `pytest-mock` para aislar dependencias externas (NewsAPI, Google Cloud Storage).
*   **Validación de Datos**: `pandera` para asegurar contratos de datos (Data Contracts).

## 🧪 Cobertura de Pruebas

Las pruebas se encuentran en el directorio `tests/` y cubren los siguientes aspectos críticos:

### 1. Ingesta de Datos (`test_ingest.py`)

Se verifica el módulo `src.data.ingest_news` para asegurar la robustez de la extracción de noticias.

*   **Variables de Entorno**: Verificación de fallo controlado si falta `NEWS_API_KEY`.
*   **Interacción con API Externa**:
    *   Simulación (Mock) de respuestas exitosas de NewsAPI.
    *   Manejo de respuestas vacías (cero artículos).
    *   Manejo de errores de conexión o formato JSON inválido.
*   **Validación de Esquema**:
    *   Se asegura que los DataFrames generados cumplan con `NewsArticleSchema` (columnas obligatorias, tipos de datos).
*   **Interacción con la Nube (GCS)**:
    *   Simulación del cliente `storage.Client`.
    *   Verificación de llamadas correctas a `upload_from_filename`.
    *   Manejo de errores si la subida falla o si `GCS_BUCKET_NAME` no está definido.

## 🚀 Ejecución de Pruebas

Para ejecutar la suite de pruebas localmente:

```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt

# Ejecutar pytest
pytest
```

## 📝 Próximos Pasos (Deuda Técnica)

*   Agregar pruebas unitarias para `src/process_sentiment.py` (Mocking del modelo FinBERT).
*   Implementar pruebas de integración end-to-end (E2E) en un entorno de staging.
