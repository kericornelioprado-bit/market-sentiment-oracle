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
