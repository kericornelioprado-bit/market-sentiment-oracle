# Infraestructura del Proyecto

Este documento detalla la infraestructura aprovisionada en Google Cloud Platform (GCP) y los recursos de Kubernetes.

## ☁️ Google Cloud Platform (Terraform)

La infraestructura base se gestiona mediante Terraform.

### Almacenamiento
* **Google Storage Bucket**: `[PROJECT_ID]-data-lake`
    * **Ubicación**: US
    * **Acceso**: Uniform Bucket Level Access (Seguridad reforzada).
    * **Propósito**: Almacenamiento de datos crudos (Raw) y procesados (Parquet/Embeddings).
* **Artifact Registry**: `market-oracle-repo`
    * **Formato**: Docker
    * **Ubicación**: us-central1

### Computación (GKE)
* **Cluster**: `primary` (market-oracle-cluster).
    * **Ubicación**: Zonal (us-central1-a)
* **Node Pool**: `spot-node-pool`
    * **Tipo de Máquina**: `e2-medium` (2 vCPU, 4GB RAM).
    * **Estrategia de Costos**: **Spot Instances** (Ahorro de costos >70%).

## 📦 Kubernetes (K8s)

Orquestación de cargas de trabajo definida en manifiestos YAML.

### CronJobs
* **`ingest-news-daily`**
    * **Frecuencia**: Lunes a Viernes a las 12:00 UTC (06:00 AM CDMX).
    * **Imagen**: `us-central1-docker.pkg.dev/market-oracle-tesis/market-oracle-repo/ingest-news:latest`
    * **Recursos**:
        * Request: 200m CPU, 256Mi RAM.
        * Limit: 500m CPU, 512Mi RAM.

* **`trading-bot`**
    * **Frecuencia**: Cada hora (`0 * * * *`).
    * **Imagen**: `us-central1-docker.pkg.dev/market-oracle-tesis/market-oracle-repo/trading-bot:v1`
    * **Secretos**: Consumen `bot-secrets` (API Keys de Alpaca).

### Jobs (Procesamiento Batch)
* **`news-ingestion-job-v2-dns-fix`**
    * **Propósito**: Ingesta manual de noticias con corrección de DNS.
    * **Imagen**: `us-central1-docker.pkg.dev/market-oracle-tesis/market-repo/market-oracle:v2`
    * **Configuración**: `dnsPolicy: Default` para resolución de nombres en la red del nodo.

* **`sentiment-processor-manual-01`**
    * **Propósito**: Ejecución del pipeline de análisis de sentimiento (FinBERT).
    * **Imagen**: `us-central1-docker.pkg.dev/market-oracle-tesis/market-oracle-repo/sentiment-processor:v1`
    * **Recursos (Optimizado)**:
        * Request: 100m CPU, 1Gi RAM (Ajustado para nodos Spot).
        * Limit: 1000m CPU, 2Gi RAM.
    * **Configuración**: Reinicio desactivado (`restartPolicy: Never`).

## 🐳 Imágenes Docker

Imágenes almacenadas en Google Artifact Registry:
1.  `ingest-news`: Scripts de extracción de NewsAPI.
2.  `sentiment-processor`: Entorno PyTorch (CPU) + Transformers para FinBERT.
3.  `market-oracle`: Imagen principal unificada (v2) para ingesta y otros procesos.
4.  `trading-bot`: Entorno de ejecución para el bot de trading (Alpaca API).
