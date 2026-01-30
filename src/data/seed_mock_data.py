import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import storage
import io
import random

# Configuración
BUCKET_NAME = "market-oracle-tesis-data-lake"  # ¡Asegúrate que coincida con tu Terraform!
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
DAYS_HISTORY = 100  # Generaremos 100 días de historia para tener suficiente para el RSI (14) y MACD (26)

def generate_mock_prices(ticker, days=DAYS_HISTORY):
    """Genera precios OHLCV simulados con tendencia aleatoria."""
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    dates.reverse() # Orden cronológico
    
    # Random walk start price
    price = 150.0 
    data = []
    
    for date in dates:
        change = np.random.normal(0, 2) # Cambio diario normal
        price += change
        if price < 10: price = 10 # Floor
        
        # Simular OHLC
        open_p = price + np.random.normal(0, 0.5)
        close_p = price # Usamos el precio final del random walk
        high_p = max(open_p, close_p) + abs(np.random.normal(0, 1))
        low_p = min(open_p, close_p) - abs(np.random.normal(0, 1))
        volume = int(np.random.normal(1000000, 200000))
        
        data.append({
            "Date": date,
            "Open": open_p,
            "High": high_p,
            "Low": low_p,
            "Close": close_p,
            "Volume": volume,
            "Ticker": ticker
        })
        
    return pd.DataFrame(data)

def generate_mock_sentiment(ticker, days=DAYS_HISTORY):
    """Genera noticias procesadas (embeddings) simuladas."""
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    data = []
    
    labels = ['positive', 'negative', 'neutral']
    
    for date in dates:
        # Simulamos entre 0 y 5 noticias por día
        num_news = random.randint(0, 5)
        
        for _ in range(num_news):
            # Asignar una hora aleatoria dentro del día
            news_date = date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            data.append({
                "date": news_date.isoformat(),
                "title": f"Mock news for {ticker} - event {_}",
                "sentiment_label": random.choice(labels),
                "sentiment_score": random.uniform(0.55, 0.99) # FinBERT suele ser confiado
            })
            
    return pd.DataFrame(data)

def upload_to_gcs(bucket, df, path):
    """Sube un DataFrame como Parquet a GCS."""
    buff = io.BytesIO()
    df.to_parquet(buff)
    buff.seek(0)
    
    blob = bucket.blob(path)
    blob.upload_from_file(buff)
    print(f"✅ Subido: gs://{bucket.name}/{path}")

def main():
    print(f"🌱 Sembrando datos mock en Bucket: {BUCKET_NAME}")
    storage_client = storage.Client()
    
    try:
        bucket = storage_client.get_bucket(BUCKET_NAME)
    except Exception as e:
        print(f"❌ Error conectando al bucket: {e}")
        print("Tip: Verifica que hiciste 'gcloud auth login' y 'terraform apply'")
        return

    for ticker in TICKERS:
        print(f"\n--- Generando para {ticker} ---")
        
        # 1. Precios (Raw)
        # Ruta esperada por merge_data.py: data/raw/prices/{ticker}_latest.parquet
        df_prices = generate_mock_prices(ticker)
        price_path = f"data/raw/prices/{ticker}_latest.parquet"
        upload_to_gcs(bucket, df_prices, price_path)
        
        # 2. Sentimiento (Processed)
        # Ruta esperada por merge_data.py: data/processed/embeddings/{ticker}_sentiment.parquet
        df_sentiment = generate_mock_sentiment(ticker)
        sentiment_path = f"data/processed/embeddings/{ticker}_sentiment.parquet"
        upload_to_gcs(bucket, df_sentiment, sentiment_path)

    print("\n✨ ¡Sembrado completo! Ahora puedes probar 'merge_data.py'")

if __name__ == "__main__":
    main()