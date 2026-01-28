# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.0] - 2026-01-28

### 🚀 Nuevas Funcionalidades
- Implementación inicial del pipeline de ingesta de noticias financieras (`ingest_news.py`).
- Implementación de descarga de datos de mercado con `yfinance` (`ingest.py`).
- Análisis de sentimiento utilizando FinBERT (`process_sentiment.py`).

### 🏗️ Infraestructura
- **Optimización GCS**: Se refactorizó el cliente de Google Cloud Storage para reutilizar la instancia y mejorar el rendimiento (`perf-gcs-client-reuse`).
- Definición de infraestructura como código (Terraform) para GKE y GCS.
- Configuración de CronJobs de Kubernetes para orquestación.

### 🧪 Testing
- Suite de pruebas inicial para la ingesta de noticias con validación de esquemas (Pandera) y mocking de APIs.
