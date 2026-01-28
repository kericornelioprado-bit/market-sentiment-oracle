# Market Sentiment Oracle: Hybrid SVM-LSTM Stock Prediction

## Descripción
Este proyecto implementa una arquitectura **MLOps híbrida** para predecir la tendencia bursátil de las "7 Magníficas" (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA).
Combina análisis de sentimiento de noticias financieras (usando **FinBERT**) con análisis técnico de series de tiempo, comparando el desempeño de **Máquinas de Soporte Vectorial (SVM)** y **Redes Neuronales Recurrentes (LSTM)**.

## 💻 Stack Tecnológico (v2.0)

**1. Entorno de Desarrollo (Dev Environment)**
* **IDE:** **Google Antigravity** (Entorno Cloud-Native).
* **OS:** Ubuntu 24.04 LTS (Subsistema WSL2/Nativo).
* **Lenguaje:** Python 3.12 (Modo estricto).
* **Gestor de Paquetes:** **uv** (Rust-based). Reemplaza a `pip` y `poetry` por su velocidad.

**2. Agentes de IA & Automatización (AI-Assisted Engineering)**
* **Jules (Code Agents):**
    * *Agente Bolt ⚡:* Optimización de rendimiento y refactorización (Lazy Loading, Singletons).
    * *Agente Sentinel 🛡️:* Guardián de seguridad (DevSecOps) y escaneo de secretos.
* **Gemini CLI:** Generación automática de pruebas unitarias y documentación.

**3. Infraestructura & MLOps (Cloud Layer)**
* **IaC:** **Terraform** (Gestión de estado remoto en GCS).
* **Contenedores:** Docker (Builds multi-etapa optimizados para CPU/GPU).
* **Orquestación:** **Google Kubernetes Engine (GKE)** con Nodos Spot.
* **Almacenamiento:** Google Cloud Storage (Data Lake) y Artifact Registry.

**4. Data Science & NLP (Core Intelligence)**
* **Procesamiento:** **PyTorch** (Versión CPU optimizada para inferencia).
* **Modelo NLP:** **FinBERT** (ProsusAI) para análisis de sentimiento.
* **Librerías Clave:** `transformers`, `pandas`, `google-cloud-storage`.

## 📚 Documentación Detallada

El mantenimiento de la documentación es gestionado automáticamente por **Chronicler**.

* [📜 CHANGELOG.md](CHANGELOG.md): Historial de cambios, nuevas funcionalidades y correcciones.
* [📊 DATA_DICTIONARY.md](DATA_DICTIONARY.md): Definición de esquemas de datos (Raw y Processed).
* [☁️ INFRASTRUCTURE.md](INFRASTRUCTURE.md): Mapa de recursos en la nube y configuración de Kubernetes.
* [🧪 TESTING.md](TESTING.md): Estrategia de pruebas y cobertura actual.

## Estructura del Proyecto
├── data/               # Datos locales (no subidos a git)
├── infra/              # Código de Infraestructura (Terraform & K8s)
├── src/                # Código Fuente Python
│   ├── data/           # Scripts de Ingesta y ETL
│   ├── models/         # Entrenamiento e Inferencia
│   └── visualization/  # Dashboard (Streamlit)
└── README.md
