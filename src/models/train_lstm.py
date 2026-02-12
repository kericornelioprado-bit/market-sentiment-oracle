import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from google.cloud import storage
from numpy.lib.stride_tricks import sliding_window_view
import io
import os
import joblib

# Configuración
BUCKET_NAME = "market-oracle-tesis-data-lake"
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
SEQ_LENGTH = 10  # Ventana de tiempo: El modelo mirará los últimos 10 días para predecir


class LSTMTrainer:
    def __init__(self, bucket_name):
        self.bucket = storage.Client().bucket(bucket_name)

    def load_data(self, ticker):
        blob = self.bucket.blob(f"data/gold/master_dataset_{ticker}.parquet")
        if not blob.exists():
            return None
        return pd.read_parquet(io.BytesIO(blob.download_as_bytes()))

    def create_sequences(self, X, y, time_steps=SEQ_LENGTH):
        """Transforma datos 2D en secuencias 3D para LSTM [Samples, Time Steps, Features]"""
        if len(X) <= time_steps:
            return np.array([]), np.array([])

        # Optimization: Use sliding_window_view to avoid slow python loop and unnecessary copying
        # X is (N, Features)
        # sliding_window_view(X, time_steps, axis=0) -> (N-T+1, Features, TimeSteps)
        X_windows = sliding_window_view(X, time_steps, axis=0)

        # We need (Samples, TimeSteps, Features) -> transpose(0, 2, 1)
        # And we need to drop the last window because there is no target y for it (y is shifted)
        X_seq = X_windows[:-1].transpose(0, 2, 1)

        # Targets start from time_steps index
        y_seq = y[time_steps:]

        return X_seq, y_seq

    def train(self, ticker):
        print(f"\n🧠 Entrenando LSTM para {ticker}...")

        df = self.load_data(ticker)
        if df is None:
            return

        # 1. Preparación de Datos
        # Target: 1 si Close sube mañana, 0 si baja
        # Optimization: Explicitly drop last row as we don't have tomorrow's price
        df = df.iloc[:-1].copy()
        df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
        df.dropna(inplace=True)

        feature_cols = [
            c for c in df.columns if c not in ["Target", "date_only", "Ticker"]
        ]
        data = df[feature_cols].values
        target = df["Target"].values

        # 2. Split (80/20) - Sin aleatoriedad por ser series de tiempo
        train_size = int(len(data) * 0.8)

        # 3. Escalamiento (MinMax es mejor para LSTM que StandardScaler)
        scaler = MinMaxScaler(feature_range=(0, 1))
        # Ajustamos solo con Train para evitar data leakage
        data_train = scaler.fit_transform(data[:train_size])
        data_test = scaler.transform(data[train_size:])

        y_train = target[:train_size]
        y_test = target[train_size:]

        # 4. Crear Secuencias (Ventanas deslizantes)
        # Importante: Esto reduce el tamaño del dataset en SEQ_LENGTH filas
        X_train_seq, y_train_seq = self.create_sequences(data_train, y_train)
        X_test_seq, y_test_seq = self.create_sequences(data_test, y_test)

        if len(X_train_seq) == 0 or len(X_test_seq) == 0:
            print(
                "⚠️ Datos insuficientes para generar secuencias. Necesitas más historial."
            )
            return

        # 5. Arquitectura del Modelo
        model = Sequential(
            [
                # Capa 1: LSTM con retorno de secuencias (si apiláramos más LSTMs)
                # Aquí false porque pasamos directo a Dense
                LSTM(
                    50,
                    return_sequences=False,
                    input_shape=(X_train_seq.shape[1], X_train_seq.shape[2]),
                ),
                Dropout(0.2),  # Regularización para evitar overfitting
                Dense(25, activation="relu"),
                Dense(1, activation="sigmoid"),  # Salida binaria (0 o 1)
            ]
        )

        model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )

        # 6. Entrenamiento con Early Stopping
        early_stop = EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        )

        model.fit(
            X_train_seq,
            y_train_seq,
            epochs=20,  # Pocas épocas para prueba rápida
            batch_size=16,
            validation_data=(X_test_seq, y_test_seq),
            callbacks=[early_stop],
            verbose=0,  # Silencioso para no ensuciar la consola
        )

        # 7. Evaluación
        loss, acc = model.evaluate(X_test_seq, y_test_seq, verbose=0)
        print(f"   🤖 LSTM Accuracy: {acc:.2%}")

        # Guardar modelo
        os.makedirs("models", exist_ok=True)
        model.save(f"models/lstm_{ticker}.keras")
        joblib.dump(scaler, f"models/scaler_lstm_{ticker}.pkl")
        print(f"   💾 Modelo guardado en models/lstm_{ticker}.keras")



def main():
    trainer = LSTMTrainer(BUCKET_NAME)
    for ticker in TICKERS:
        trainer.train(ticker)

if __name__ == "__main__":
    main()
