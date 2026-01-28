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

## 🚀 Ejecución de Pruebas

Para ejecutar la suite de pruebas localmente:

```bash
# Sincronizar entorno
uv sync

# Ejecutar pytest
uv run pytest
