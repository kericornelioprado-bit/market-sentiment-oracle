import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google.cloud import storage
import io
import tensorflow as tf
import joblib
from pathlib import Path

# Configuración de página
st.set_page_config(layout="wide", page_title="Market Sentiment Oracle 🔮")

# Constantes
BUCKET_NAME = "market-oracle-tesis-data-lake"
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]


@st.cache_data
def load_data(ticker):
    """Descarga datos cacheados para no ir a GCS en cada clic"""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # Cargar Precios + Indicadores (Gold Layer)
    blob_path = f"data/gold/master_dataset_{ticker}.parquet"
    blob = bucket.blob(blob_path)
    if not blob.exists():
        return None

    data = blob.download_as_bytes()
    df = pd.read_parquet(io.BytesIO(data))
    return df


@st.cache_resource
def load_model(ticker):
    """Carga el modelo LSTM y el scaler entrenados"""
    try:
        # Secure path handling to prevent directory traversal
        base_dir = Path("models").resolve()

        # Construct absolute paths
        model_path = base_dir.joinpath(f"lstm_{ticker}.keras").resolve()
        scaler_path = base_dir.joinpath(f"scaler_lstm_{ticker}.pkl").resolve()

        # Validate paths are strictly within the models directory
        if not model_path.is_relative_to(base_dir) or not scaler_path.is_relative_to(
            base_dir
        ):
            # Log this security event if logging was configured
            return None, None

        # Check existence before loading
        if not model_path.exists() or not scaler_path.exists():
            return None, None

        model = tf.keras.models.load_model(str(model_path))
        scaler = joblib.load(str(scaler_path))
        return model, scaler
    except Exception:
        return None, None


def make_prediction(model, scaler, df):
    """Genera la predicción para 'mañana' usando los últimos 10 días"""
    SEQ_LEN = 10
    if len(df) < SEQ_LEN:
        return 0.5  # Sin datos suficientes

    # Preparar features
    feature_cols = [
        c for c in df.columns if c not in ["Target", "date_only", "Ticker", "Date"]
    ]
    last_sequence = df[feature_cols].tail(SEQ_LEN).values

    # Escalar
    last_sequence_scaled = scaler.transform(last_sequence)

    # Reshape a (1, 10, features)
    X_input = last_sequence_scaled.reshape(1, SEQ_LEN, len(feature_cols))

    # Predecir
    prob = model.predict(X_input, verbose=0)[0][0]
    return prob


# --- INTERFAZ ---
st.title("🦉 Market Sentiment Oracle")
st.markdown("### Tesis de Maestría: Predicción Bursátil Híbrida (NLP + LSTM)")

# Sidebar
selected_ticker = st.sidebar.selectbox("Selecciona un Activo", TICKERS)

# Cargar datos
df = load_data(selected_ticker)

if df is not None:
    # Métricas Principales
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    diff = latest["Close"] - prev["Close"]
    diff_pct = (diff / prev["Close"]) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Precio Cierre", f"${latest['Close']:.2f}", f"{diff:.2f} ({diff_pct:.2f}%)"
    )
    col2.metric("RSI (14)", f"{latest['rsi_14']:.2f}", delta=None)
    col3.metric(
        "Sentimiento Diario",
        f"{latest['daily_sentiment']:.2f}",
        delta_color="off",
        help="Rango: -1 (Negativo) a 1 (Positivo)",
    )

    # Predicción IA
    model, scaler = load_model(selected_ticker)
    if model:
        prob = make_prediction(model, scaler, df)
        sentiment = "🟢 ALCISTA" if prob > 0.5 else "🔴 BAJISTA"
        confidence = abs(prob - 0.5) * 2  # Escalar a 0-100% de fuerza
        col4.metric("Predicción IA", sentiment, f"Confianza: {confidence:.1%}")
    else:
        col4.warning("Modelo no encontrado")

    # Gráficos
    st.subheader("Gráfico Técnico & Sentimiento")

    # Candlestick
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Precio",
        )
    )

    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["bb_upper"],
            line=dict(color="gray", width=1),
            name="BB Upper",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["bb_lower"],
            line=dict(color="gray", width=1),
            name="BB Lower",
        )
    )

    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Data Table
    with st.expander("Ver Datos Crudos"):
        st.dataframe(df.tail(20))

else:
    st.error("No se encontraron datos. Ejecuta el pipeline de datos primero.")
