import pandas as pd
from google.cloud import storage
import io
import datetime

# Configuración
BUCKET_NAME = "market-oracle-tesis-data-lake" 
TODAY = datetime.datetime.now().strftime("%Y-%m-%d")

def upload_synthetic_data():
    print(f"🧪 Generando datos de prueba para fecha: {TODAY}")
    
    # Simulación de noticias financieras (Títulos en inglés)
    data = {
        "date": [TODAY] * 5,
        "symbol": ["AAPL", "AAPL", "TSLA", "GOOGL", "AMZN"],
        "title": [
            "Apple reports record breaking quarter earnings, stock soars", # Debería ser Positivo
            "iPhone 16 production delayed due to supply chain issues",     # Debería ser Negativo
            "Tesla autopilot causes minor accident in California",         # Debería ser Negativo
            "Google announces new AI partnership with medical centers",    # Debería ser Positivo
            "Amazon maintains steady growth in cloud sector"               # Debería ser Neutral/Positivo
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Subir a GCS simulando la estructura real
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    
    symbols = df["symbol"].unique()
    
    for symbol in symbols:
        subset = df[df["symbol"] == symbol]
        blob_name = f"data/raw/{symbol}/{TODAY}.parquet"
        
        # Convertir a Parquet en memoria
        buffer = io.BytesIO()
        subset.to_parquet(buffer, index=False)
        
        blob = bucket.blob(blob_name)
        blob.upload_from_file(buffer, rewind=True)
        print(f"✅ Subido: gs://{BUCKET_NAME}/{blob_name}")

if __name__ == "__main__":
    upload_synthetic_data()