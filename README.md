# Market Sentiment Oracle: Hybrid SVM-LSTM Stock Prediction

## Descripción
Este proyecto implementa una arquitectura **MLOps híbrida** para predecir la tendencia bursátil de las "7 Magníficas" (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA).
Combina análisis de sentimiento de noticias financieras (usando **FinBERT**) con análisis técnico de series de tiempo, comparando el desempeño de **Máquinas de Soporte Vectorial (SVM)** y **Redes Neuronales Recurrentes (LSTM)**.

## Arquitectura Tecnológica
* **Infraestructura:** Google Cloud Platform (GCP), Terraform (IaC), Kubernetes (GKE).
* **Orquestación:** Docker, CronJobs.
* **Modelado:** PyTorch (FinBERT), TensorFlow (LSTM), Scikit-learn (SVM).
* **Validación:** Walk-Forward Validation y Backtrader.

## 📚 Documentación Detallada

El mantenimiento de la documentación es gestionado automáticamente por **Chronicler**.

*   [📜 CHANGELOG.md](CHANGELOG.md): Historial de cambios, nuevas funcionalidades y correcciones.
*   [📊 DATA_DICTIONARY.md](DATA_DICTIONARY.md): Definición de esquemas de datos (Raw y Processed).
*   [☁️ INFRASTRUCTURE.md](INFRASTRUCTURE.md): Mapa de recursos en la nube y configuración de Kubernetes.
*   [🧪 TESTING.md](TESTING.md): Estrategia de pruebas y cobertura actual.

## Estructura del Proyecto
├── data/               # Datos locales (no subidos a git)
├── infra/              # Código de Infraestructura (Terraform & K8s)
├── src/                # Código Fuente Python
│   ├── data/           # Scripts de Ingesta y ETL
│   ├── models/         # Entrenamiento e Inferencia
│   └── visualization/  # Dashboard (Streamlit)
└── README.md
