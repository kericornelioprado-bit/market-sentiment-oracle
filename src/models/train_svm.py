import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import io
from google.cloud import storage
import os

# Configuración
BUCKET_NAME = "market-oracle-tesis-data-lake"  # Ajusta si es necesario
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]


class SVMTrainer:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    def load_data(self, ticker):
        """Descarga el Dataset Maestro de la capa Gold."""
        blob_path = f"data/gold/master_dataset_{ticker}.parquet"
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            print(f"⚠️ No se encontró datos para {ticker}")
            return None

        data = blob.download_as_bytes()
        df = pd.read_parquet(io.BytesIO(data))
        return df

    def prepare_features(self, df):
        """Genera X (Features) e Y (Target)."""
        df = df.copy()

        # 1. Crear Target: ¿El precio subirá MAÑANA?
        # Shift(-1) mira al futuro (solo para entrenar, prohibido en inferencia)
        df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

        # Eliminamos la última fila porque no tiene 'mañana'
        df.dropna(inplace=True)

        # 2. Seleccionar Features
        # Excluimos columnas que no son predictoras (fechas, el target mismo)
        drop_cols = [
            "Target",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Ticker",
            "date_only",
        ]
        features = [c for c in df.columns if c not in drop_cols]

        X = df[features]
        y = df["Target"]

        return X, y

    def train(self, ticker):
        print(f"\n🚀 Entrenando SVM para {ticker}...")

        df = self.load_data(ticker)
        if df is None:
            return

        X, y = self.prepare_features(df)

        # 3. Split respetando el tiempo (Sin aleatoriedad)
        # Los primeros 80% días para entrenar, el 20% final para probar
        train_size = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
        y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

        # 4. Escalamiento (CRÍTICO para SVM)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 5. Optimización de Hiperparámetros (GridSearch)
        # Buscamos la mejor combinación de C (penalización) y gamma (influencia)
        param_grid = {
            "C": [0.1, 1, 10, 100],
            "gamma": [1, 0.1, 0.01, 0.001],
            "kernel": ["rbf", "sigmoid"],  # Probamos radial y sigmoide
        }

        # TimeSeriesSplit para validación cruzada sin mirar al futuro
        tscv = TimeSeriesSplit(n_splits=3)

        grid = GridSearchCV(SVC(), param_grid, refit=True, verbose=0, cv=tscv)
        grid.fit(X_train_scaled, y_train)

        # 6. Evaluación
        print(f"   🏆 Mejores parámetros: {grid.best_params_}")
        y_pred = grid.predict(X_test_scaled)

        acc = accuracy_score(y_test, y_pred)
        print(f"   🎯 Accuracy en Test: {acc:.2%}")
        print("   📊 Reporte de Clasificación:")
        print(classification_report(y_test, y_pred))

        # 7. Guardar Modelo y Scaler (Serialización)
        # Guardamos localmente temporalmente y luego podríamos subir a GCS/MLflow
        os.makedirs("models", exist_ok=True)
        joblib.dump(grid.best_estimator_, f"models/svm_{ticker}.pkl")
        joblib.dump(scaler, f"models/scaler_{ticker}.pkl")
        print(f"   💾 Modelo guardado en models/svm_{ticker}.pkl")


if __name__ == "__main__":
    trainer = SVMTrainer(BUCKET_NAME)

    # Entrenar para todos los tickers
    for ticker in TICKERS:
        trainer.train(ticker)
