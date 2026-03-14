# Notas para el Paper: Síntesis por Rúbrica

Este documento agrupa la información del repositorio estructurada directamente según las secciones de la rúbrica del paper. El objetivo es facilitar la redacción final, proporcionando los argumentos técnicos y metodológicos necesarios para alcanzar la máxima puntuación en cada apartado.

---

## 1. Metodología: Etapas de Modelado, Validación y Aprendizaje Automático (50 Puntos)

Para obtener la calificación de **Excelente (45-50)**, la metodología descrita en el paper debe ser explícita, detallada y rigurosa. El repositorio actual proporciona evidencia sólida en cada una de estas etapas:

### A. Ingesta y Preprocesamiento de Datos (Rigor Multimodal)
El sistema no se basa en un dataset estático descargado manualmente (típico de un *notebook* básico), sino que implementa *pipelines* de extracción automatizados y robustos:
1.  **Datos de Mercado (Series Temporales):**
    *   Se descargan datos OHLCV de Yahoo Finance de los últimos 5 años para las "7 Magníficas" (`src/data/ingest.py`).
    *   **Rigor:** La ingesta masiva se optimiza mediante peticiones por lotes (`group_by='ticker'`), logrando un aumento de rendimiento de más de 10x. Se aplican técnicas de limpieza (`df.dropna(how='all')`) para alinear correctamente los historiales de negociación y manejar valores nulos introducidos por la asincronía de los mercados.
2.  **Datos No Estructurados (Noticias y Sentimiento):**
    *   Se extraen noticias financieras mediante la API de NewsAPI (`src/data/ingest_news.py`).
    *   **Validación Estricta:** Se emplea la librería `pandera` para definir un esquema estricto (`NewsArticleSchema`) que valida la integridad de los datos entrantes (ej. obligatoriedad de título, URL válida, timestamp de extracción).
    *   **Procesamiento de Lenguaje Natural (NLP):** Un modelo FinBERT pre-entrenado procesa los titulares para extraer el sentimiento del mercado (`src/process_sentiment.py`). Este proceso utiliza inferencia por lotes (batching) y aceleración por GPU, convirtiendo el texto en una señal numérica continua.

### B. Ingeniería de Características (Feature Engineering)
La fusión de señales de distintas naturalezas es el núcleo del modelado predictivo del proyecto (`src/features/`):
*   **Indicadores Técnicos (`src/features/technical_indicators.py`):** Se calculan variables como RSI, MACD y Bandas de Bollinger para capturar el momento y la tendencia. Se destaca la optimización matemática del cálculo del RSI para prevenir errores de división por cero y mejorar el rendimiento.
*   **Alineación Temporal (`src/features/merge_data.py`):** Se orquesta la fusión ("DataMerger") de los datos de mercado asíncronos con el sentimiento intradiario, agregando este último mediante un "promedio ponderado por confianza" para crear una única señal diaria ("Master Dataset").

### C. Modelado de Machine Learning y Prevención de Fuga de Datos
El proyecto evalúa dos enfoques computacionales contrastantes para la predicción de series temporales ("¿Subirá el precio mañana?"):
1.  **Modelo Lineal (SVM - Máquinas de Soporte Vectorial):** En `src/models/train_svm.py`, se entrena un modelo con kernel RBF.
    *   **Validación Rigurosa:** A diferencia de una validación cruzada estándar (que mezcla el futuro con el pasado), el sistema utiliza `TimeSeriesSplit` y `GridSearchCV` para optimizar hiperparámetros de forma estrictamente secuencial.
2.  **Modelo Profundo (LSTM - Redes Neuronales Recurrentes):** En `src/models/train_lstm.py`, se captura la dependencia temporal compleja de los datos fusionados.
    *   **Ingeniería Avanzada:** La generación de secuencias de entrada (ventanas de tiempo) para la LSTM se optimiza a nivel de memoria utilizando `numpy.lib.stride_tricks.sliding_window_view`, logrando mejoras de rendimiento exponenciales.
    *   **Construcción del Target:** En ambos modelos, el target se define truncando la última fila del dataset en lugar de eliminar los valores nulos generados por el desplazamiento (`shift`). Esto previene sesgos e inconsistencias en el entrenamiento.

---

## 2. Análisis y Comparación de Resultados (25 Puntos)

Para lograr un análisis **Excelente (21-25)**, el paper debe trascender las métricas de clasificación tradicionales e interpretar el impacto financiero del modelo:

*   **Comparación de Arquitecturas (SVM vs. LSTM):** El diseño del repositorio permite una discusión profunda entre la interpretabilidad y velocidad de entrenamiento de un modelo lineal con kernel RBF (SVM) frente a la capacidad de un modelo secuencial profundo (LSTM) para capturar patrones a largo plazo en series financieras ruidosas.
*   **Métricas Estándar vs. Financieras:** Si bien el sistema evalúa los modelos mediante `classification_report`, `confusion_matrix` y `accuracy_score`, el análisis de resultados adquiere verdadero valor gracias al módulo de **Backtesting** (`src/backtesting/strategy.py`).
*   **Interpretación Práctica:** El backtesting permite simular la ejecución histórica de las predicciones del modelo ("trading de papel"), facilitando un análisis de escenarios realista. Se puede discutir cómo un modelo con una "precisión moderada" en clasificación puede, no obstante, generar retornos positivos en backtesting si captura correctamente las tendencias fuertes (momentos de alto sentimiento positivo o sobreventa en RSI).

---

## 3. Justificación Arquitectónica: De la Experimentación (Notebook) a Producción (MLOps)

*Esta sección aporta un enorme valor agregado al paper, demostrando madurez en la ingeniería de software y justificando la mantenibilidad a largo plazo del sistema.*

A diferencia de un proyecto académico tradicional que finaliza en un Jupyter Notebook monolítico, este repositorio implementa un **Sistema MLOps Híbrido** diseñado para la producción:

1.  **Reproducibilidad y Aislamiento (Docker):**
    *   Los componentes (ingesta, procesamiento, bot de ejecución) están contenedorizados.
    *   Los `Dockerfiles` emplean construcciones multi-etapa (multi-stage builds) para crear imágenes ligeras y seguras (ejecución sin privilegios de *root* mediante el usuario `appuser`).
2.  **Orquestación Continua (Kubernetes):**
    *   La infraestructura en `infra/k8s/` utiliza *CronJobs* para programar la ejecución autónoma de las etapas de extracción, fusión y predicción, replicando el comportamiento de un sistema financiero real que opera diariamente, en lugar de una ejecución manual estática.
3.  **Calidad del Software y Pruebas Automatizadas (CI/CD):**
    *   El repositorio cuenta con una extensa suite de **más de 30 pruebas unitarias y de integración** (`tests/`).
    *   **Rigor de Pruebas:** Se utilizan técnicas avanzadas de simulación (*mocking* a través de `unittest.mock`) para aislar el acceso a APIs de red (Yahoo Finance, NewsAPI) y almacenamiento en la nube (GCS), garantizando que el pipeline de ML pueda ser validado continuamente sin depender de servicios externos o incurrir en costos.
4.  **Ejecución Autónoma (Trading Bot):**
    *   El módulo `src/execution/bot.py` cierra el ciclo conectando las señales de los modelos validados directamente con la API de Alpaca Markets, automatizando la ejecución de órdenes de mercado.
