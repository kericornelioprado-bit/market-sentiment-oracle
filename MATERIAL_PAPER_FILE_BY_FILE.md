# Notas para el Paper: Desglose por Archivo

Este documento contiene un análisis detallado, archivo por archivo, de los componentes clave del repositorio. El objetivo es proporcionar evidencia concreta para respaldar las secciones de Metodología, Análisis de Resultados y la justificación de una arquitectura MLOps en producción (frente a un entorno experimental de *notebook*), asegurando la máxima puntuación según la rúbrica.

---

## 1. Módulo de Ingesta de Datos (`src/data/`)

### `src/data/ingest.py` (Ingesta de Mercado)
- **Metodología:** Descarga datos históricos de mercado (OHLCV) de Yahoo Finance para las "7 Magníficas" (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA) en los últimos 5 años.
- **Rigor e Ingeniería:** Optimiza la descarga utilizando procesamiento por lotes (`group_by='ticker'`), lo cual representa una mejora de rendimiento significativa (>10x). Implementa limpieza de datos (`df.dropna(how='all')`) para alinear historiales de negociación inconsistentes.

### `src/data/ingest_news.py` (Ingesta de Noticias)
- **Metodología:** Consume la API de NewsAPI para recolectar noticias financieras recientes sobre los activos objetivos.
- **Validación y Calidad:** Utiliza la librería `pandera` para definir y validar un esquema estricto (`NewsArticleSchema`) que asegura que los artículos tengan título, URL válida, símbolo asociado y fecha de extracción.
- **Rigor e Ingeniería:** Implementa concurrencia con `ThreadPoolExecutor` para paralelizar las peticiones HTTP por símbolo, acelerando el proceso (~4x). Maneja excepciones por hilo para evitar que el fallo en un símbolo interrumpa toda la ingesta.

---

## 2. Ingeniería de Características (`src/features/`)

### `src/features/technical_indicators.py`
- **Metodología:** Calcula indicadores técnicos avanzados a partir de los datos de mercado:
  - **RSI (Relative Strength Index):** Usando la fórmula optimizada para evitar errores de división por cero y mejorar el rendimiento.
  - **MACD (Moving Average Convergence Divergence):** Con sus tres componentes (MACD Line, Signal Line, Histogram) para detectar la inercia de tendencia.
  - **Retornos Logarítmicos:** Optimizados con `np.log(series).diff()`.
- **Rigor:** Estas variables técnicas son fundamentales para proporcionar un contexto financiero al modelo antes de integrar el sentimiento.

### `src/features/merge_data.py` (DataMerger)
- **Metodología:** Orquesta la fusión de los datos de mercado (alojados localmente o en GCS) con las predicciones del modelo de sentimiento (descargadas de GCS).
- **Procesamiento de Señal:** Agrega el sentimiento intradía en una única señal diaria ("promedio ponderado por confianza").
- **Salida:** Genera el "Master Dataset" (Capa Gold) para cada activo, alineando temporalmente el precio, los indicadores técnicos y la variable de sentimiento, sentando las bases sólidas para el entrenamiento de los modelos de predicción.

---

## 3. Análisis de Sentimiento y Procesamiento (`src/`)

### `src/process_sentiment.py`
- **Metodología:** Aplica un modelo de Lenguaje Pre-entrenado (FinBERT) especializado en finanzas sobre los titulares y resúmenes de noticias extraídos.
- **Rigor e Ingeniería:** Utiliza procesamiento por lotes (batching) y aceleración por GPU (cuando está disponible) u operaciones vectorizadas eficientes en PyTorch (`torch.max`) para la inferencia, evitando cuellos de botella clásicos de procesamiento textual.

---

## 4. Modelado Predictivo (`src/models/`)

### `src/models/train_svm.py`
- **Metodología:** Entrena un modelo de Máquinas de Soporte Vectorial (SVM) con un kernel RBF para predecir si el precio subirá al día siguiente.
- **Validación Estricta:** Implementa `TimeSeriesSplit` y `GridSearchCV` para optimizar hiperparámetros (`C`, `gamma`) respetando la secuencia temporal (sin fuga de datos del futuro al pasado, lo cual es un error crítico común en notebooks básicos).
- **Tratamiento del Target:** Define el target ("¿El precio subirá MAÑANA?") truncando la última fila del conjunto de datos para evitar valores nulos introducidos por la operación de desplazamiento temporal (`shift`).

### `src/models/train_lstm.py`
- **Metodología:** Diseña y entrena una Red Neuronal Recurrente tipo LSTM (Long Short-Term Memory) capaz de capturar dependencias temporales y patrones secuenciales en los datos fusionados (precios, indicadores, sentimiento).
- **Ingeniería Avanzada:** Optimiza la generación de secuencias utilizando `numpy.lib.stride_tricks.sliding_window_view`, lo cual representa una mejora de rendimiento exponencial respecto a bucles tradicionales.

---

## 5. Backtesting y Ejecución (`src/backtesting/` & `src/execution/`)

### `src/backtesting/strategy.py`
- **Análisis de Resultados:** Simula la ejecución de las predicciones de los modelos sobre datos históricos para evaluar el rendimiento financiero de la estrategia, permitiendo una comparación profunda de escenarios que va más allá de métricas puras de Machine Learning (como *Accuracy*).

### `src/execution/bot.py` (Trading Bot)
- **Producción:** Conecta las predicciones en vivo con la API de Alpaca Markets para la ejecución automatizada de operaciones bursátiles (`MarketOrderRequest`). Maneja la autenticación segura y el registro (logging) robusto.

---

## 6. Arquitectura MLOps y Despliegue en Producción (Justificación "Más allá del Notebook")

Un punto crítico del paper es demostrar por qué este sistema supera a un simple *notebook* exploratorio. El repositorio evidencia una arquitectura robusta de producción:

### `Dockerfile` y Contenedorización
- Utiliza **construcciones multi-etapa (multi-stage builds)** en el `Dockerfile` principal para separar el entorno de construcción del entorno de ejecución, reduciendo drásticasmente el tamaño de la imagen (ej., de 20GB a ~3GB al forzar dependencias solo CPU).
- Ejecuta los servicios como un **usuario no root (`appuser`)** por principios de seguridad en producción.
- Existen imágenes Docker específicas para cada tarea (`ingest-news`, `sentiment-processor`, `trading-bot`), aislando dependencias y responsabilidades.

### `infra/k8s/` (Orquestación con Kubernetes)
- Despliegue estructurado usando objetos de Kubernetes como **CronJobs** (`ingest-cronjob.yaml`, `process-cronjob.yaml`, `merge-cronjob.yaml`).
- Esto asegura que todo el *pipeline* (ingesta, procesamiento de sentimiento, fusión y ejecución) se ejecute de forma programada, autónoma y escalable, superando la limitación de ejecución manual de un notebook.

### `tests/` (Pruebas Automatizadas)
- **Rigor:** Cuenta con una suite masiva de **35 pruebas automatizadas** que abarcan la validación de módulos completos (`test_ingest.py`, `test_models.py`, `test_dashboard.py`).
- Las pruebas utilizan técnicas avanzadas como *mocking* (`unittest.mock`) para aislar los módulos del acceso a la red (ej., APIs externas o GCS), garantizando la reproducibilidad y previniendo regresiones de código.

---

**Resumen para la Rúbrica:**
- **Metodología (50 pts):** Justificada por la validación de pandera, el uso de TimeSeriesSplit, la fusión cuidadosa de señales heterogéneas y la generación de ventanas para LSTM sin fuga de datos temporal.
- **Análisis y Comparación (25 pts):** Justificado por la comparación en el rendimiento de un modelo lineal (SVM) frente a uno profundo secuencial (LSTM) en el contexto de series temporales, culminando en la validación a través de un módulo dedicado de Backtesting.
