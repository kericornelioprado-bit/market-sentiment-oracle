# Diccionario de Datos

Este documento describe los esquemas de datos utilizados en el proyecto `market-sentiment-oracle`.

## 📰 Datos de Noticias (Raw)

Datos obtenidos a través de NewsAPI y almacenados en formato Parquet.

| Columna | Tipo | Origen | Descripción |
| :--- | :--- | :--- | :--- |
| `publishedAt` | DateTime | NewsAPI | Fecha y hora de publicación del artículo. |
| `title` | String | NewsAPI | Título del artículo noticioso. |
| `url` | String | NewsAPI | URL original del artículo. |
| `content` | String | NewsAPI | Contenido textual del artículo (puede ser nulo). |
| `symbol` | String | Ingesta | Símbolo bursátil asociado (ej. AAPL, MSFT). |
| `fetched_at` | DateTime | Ingesta | Marca de tiempo de cuando se realizó la extracción. |

> **Validación**: Definida por `NewsArticleSchema` (Pandera).
> - `title`: No puede estar vacío.
> - `url`: Debe comenzar con "http".

## 📈 Datos de Mercado (Raw)

Datos históricos OHLCV descargados de Yahoo Finance.

| Columna | Tipo | Origen | Descripción |
| :--- | :--- | :--- | :--- |
| `Date` | DateTime (Index) | Yahoo Finance | Fecha de la sesión bursátil. |
| `Open` | Float | Yahoo Finance | Precio de apertura. |
| `High` | Float | Yahoo Finance | Precio máximo de la sesión. |
| `Low` | Float | Yahoo Finance | Precio mínimo de la sesión. |
| `Close` | Float | Yahoo Finance | Precio de cierre. |
| `Adj Close` | Float | Yahoo Finance | Precio de cierre ajustado por dividendos/splits. |
| `Volume` | Int | Yahoo Finance | Volumen de acciones negociadas. |

## 🧠 Datos Procesados (Sentiment Analysis)

Datos enriquecidos con análisis de sentimiento utilizando FinBERT.

| Columna | Tipo | Origen | Descripción |
| :--- | :--- | :--- | :--- |
| `sentiment_label` | String | FinBERT | Categoría de sentimiento: `positive`, `negative`, `neutral`. |
| `sentiment_score` | Float | FinBERT | Puntuación de confianza de la predicción (0.0 - 1.0, Softmax). |

> **Nota**: Estos campos se añaden al esquema de Noticias Raw durante el procesamiento.

## 🏆 Datos Maestros (Gold/Features)

Dataset consolidado para entrenamiento de modelos, generado por `merge_data.py`. Incluye precios, indicadores técnicos y sentimiento.

| Columna | Tipo | Origen | Descripción |
| :--- | :--- | :--- | :--- |
| `log_returns` | Float | Features | Retornos logarítmicos del precio de cierre. |
| `rsi_14` | Float | Features | Índice de Fuerza Relativa (RSI, 14 periodos). |
| `macd_line` | Float | Features | Línea MACD (Diferencia de EMAs). |
| `macd_signal` | Float | Features | Línea de Señal del MACD. |
| `macd_hist` | Float | Features | Histograma MACD (MACD - Señal). |
| `bb_upper` | Float | Features | Banda Superior de Bollinger. |
| `bb_lower` | Float | Features | Banda Inferior de Bollinger. |
| `bb_width` | Float | Features | Ancho de Bandas de Bollinger (Volatilidad relativa). |
| `volatility_21d` | Float | Features | Volatilidad histórica (Desviación estándar móvil 21 días). |
| `daily_sentiment` | Float | Features | Sentimiento diario promedio ponderado por confianza. |
| `news_volume` | Int | Features | Cantidad de noticias procesadas en el día. |
| `Target` | Int | Calculated (Train) | 1 si el precio de cierre del día siguiente es mayor al actual, 0 en caso contrario. |

> **Nota sobre Entrenamiento**: La columna `Target` se genera dinámicamente durante el proceso de entrenamiento en `train_lstm.py`.
