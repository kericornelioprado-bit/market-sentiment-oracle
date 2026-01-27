import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.cloud import storage # <--- Nueva importación

# Cargar variables
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")
# Leemos el nombre del bucket desde una variable de entorno (que configuraremos en Kubernetes)
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME") 

def upload_to_gcs(source_file_name, destination_blob_name):
    """Sube un archivo al bucket de Google Cloud Storage."""
    if not BUCKET_NAME:
        print("⚠️ No se definió GCS_BUCKET_NAME. Saltando subida a la nube.")
        return

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)
        print(f"☁️ Archivo subido exitosamente a: gs://{BUCKET_NAME}/{destination_blob_name}")
    except Exception as e:
        print(f"❌ Error subiendo a GCS: {e}")

def fetch_news():
    if not API_KEY:
        raise ValueError("❌ No se encontró la API Key en el .env")
    
    # Definir fechas (últimos 3 días para asegurar datos)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
    
    # Asegurar directorio local
    output_dir = "data/raw/news"
    os.makedirs(output_dir, exist_ok=True)

    print(f"--- Descargando Noticias desde {start_date.date()} ---")

    for symbol in symbols:
        print(f"📡 Buscando noticias para: {symbol}...")
        
        url = (
            f"https://newsapi.org/v2/everything?"
            f"q={symbol}&"
            f"from={start_date.date()}&"
            f"sortBy=publishedAt&"
            f"language=en&"
            f"apiKey={API_KEY}"
        )
        
        response = requests.get(url)
        data = response.json()
        
        articles = data.get("articles", [])
        
        if articles:
            # Convertir a DataFrame
            df = pd.DataFrame(articles)
            df['symbol'] = symbol
            df['fetched_at'] = datetime.now()
            
            # 1. Guardar localmente (formato Parquet)
            filename = f"{symbol}_news.parquet"
            local_path = os.path.join(output_dir, filename)
            df.to_parquet(local_path, index=False)
            print(f"✅ Guardado local: {local_path} ({len(df)} artículos)")
            
            # 2. Subir a la nube (Google Cloud Storage)
            # Guardamos con estructura de carpetas: raw/news/YYYY-MM-DD/AAPL.parquet
            date_folder = datetime.now().strftime("%Y-%m-%d")
            gcs_path = f"raw/news/{date_folder}/{filename}"
            upload_to_gcs(local_path, gcs_path)
            
        else:
            print(f"⚠️ No se encontraron noticias recientes para {symbol}")

if __name__ == "__main__":
    fetch_news()