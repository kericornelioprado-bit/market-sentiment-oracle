# Infraestructura del Proyecto

Este documento detalla la infraestructura aprovisionada en Google Cloud Platform (GCP) y los recursos de Kubernetes.

## ☁️ Google Cloud Platform (Terraform)

La infraestructura base se gestiona mediante Terraform.

### Almacenamiento
*   **Google Storage Bucket**: `[PROJECT_ID]-data-lake`
    *   **Ubicación**: US
    *   **Acceso**: Uniform Bucket Level Access (Seguridad reforzada).
    *   **Propósito**: Almacenamiento de datos crudos (Raw) y procesados (Parquet).

### Computación (GKE)
*   **Cluster**: `primary` (Nombre definido por variable).
    *   **Ubicación**: Zonal (a)
    *   **Configuración**: Eliminación del pool por defecto.
*   **Node Pool**: `spot-node-pool`
    *   **Tipo de Máquina**: `e2-medium` (2 vCPU, 4GB RAM).
    *   **Estrategia de Costos**: **Spot Instances** (Instancias preemptibles para ahorro de costos).
    *   **Escalado Inicial**: 1 nodo.

## 📦 Kubernetes (K8s)

Orquestación de cargas de trabajo definida en manifiestos YAML.

### CronJobs
*   **`ingest-news-daily`**
    *   **Frecuencia**: Lunes a Viernes a las 12:00 UTC (06:00 AM CDMX).
    *   **Imagen**: `us-central1-docker.pkg.dev/market-oracle-tesis/market-repo/ingest-news:latest`
    *   **Recursos**:
        *   Request: 200m CPU, 256Mi RAM.
        *   Limit: 500m CPU, 512Mi RAM.
    *   **Configuración**: Tolerancia a nodos Spot.

### Jobs (Procesamiento Batch)
*   **`news-ingestion-job-v2-dns-fix`**
    *   **Propósito**: Ingesta manual o one-off.
    *   **Imagen**: `market-oracle:v2`
    *   **Nota**: Configurado con `dnsPolicy: Default` para resolución de nombres a nivel nodo.
*   **`sentiment-processor-manual-01`**
    *   **Propósito**: Ejecución del pipeline de análisis de sentimiento (FinBERT).
    *   **Imagen**: `sentiment-processor:v1`
    *   **Recursos**: Requiere más memoria (Request: 1Gi, Limit: 2Gi) para cargar el modelo de ML.

## 🐳 Imágenes Docker

Imágenes almacenadas en Google Artifact Registry:
1.  `ingest-news`: Contiene scripts de extracción de NewsAPI.
2.  `market-oracle`: Imagen base general (v2).
3.  `sentiment-processor`: Contiene PyTorch y Transformers para FinBERT.
