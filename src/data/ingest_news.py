import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.cloud import storage

# --- CORRECCIÓN DE IMPORTACIONES PANDERA ---
# Importamos todo desde pandera.pandas para evitar el FutureWarning
from pandera.pandas import DataFrameModel, Field, check, typing
from pandera.errors import SchemaError

# Cargar variables
load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

_storage_client = None

def get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client

# --- Definición del Esquema de Validación ---
class NewsArticleSchema(DataFrameModel):
    """
    Esquema de validación para los datos de noticias.
    """
    publishedAt: typing.Series[typing.DateTime] = Field(nullable=False)
    title: typing.Series[typing.String] = Field(nullable=False)
    url: typing.Series[typing.String] = Field(nullable=False)
    content: typing.Series[typing.String] = Field(nullable=True)
    symbol: typing.Series[typing.String] = Field(nullable=False)
    fetched_at: typing.Series[typing.DateTime] = Field(nullable=False)
    
    class Config:
        strict = "filter" 
        coerce = True

    # --- Validadores Personalizados ---
    @check("title", name="titulo_no_vacio")
    def check_title_not_empty(cls, series: typing.Series[typing.String]) -> typing.Series[bool]:
        return series.str.strip() != ""

    @check("url", name="url_valida")
    def check_url_starts_with_http(cls, series: typing.Series[typing.String]) -> typing.Series[bool]:
        return series.str.startswith("http")

def upload_to_gcs(source_file_name, destination_blob_name):
    if not BUCKET_NAME:
        print("⚠️ No se definió GCS_BUCKET_NAME. Saltando subida a la nube.")
        return
    try:
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        print(f"☁️ Archivo subido exitosamente a: gs://{BUCKET_NAME}/{destination_blob_name}")
    except Exception as e:
        print(f"❌ Error subiendo a GCS: {e}")

def fetch_news(symbols=None):
    if not API_KEY:
        raise ValueError("❌ No se encontró la API Key en el .env")
    
    if symbols is None:
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]
        
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    output_dir = "data/raw/news"
    os.makedirs(output_dir, exist_ok=True)

    print(f"--- Descargando Noticias desde {start_date.date()} ---")

    for symbol in symbols:
        print(f"📡 Buscando noticias para: {symbol}...")
        
        url = (
            f"https://newsapi.org/v2/everything?"
            f"q={symbol}&from={start_date.date()}&sortBy=publishedAt&"
            f"language=en&apiKey={API_KEY}"
        )
        response = requests.get(url)
        data = response.json()
        articles = data.get("articles", [])
        
        if articles:
            df = pd.DataFrame(articles)
            df['symbol'] = symbol
            df['fetched_at'] = datetime.now()

            try:
                print(f"🔍 Validando {len(df)} artículos para {symbol}...")
                df_validated = NewsArticleSchema.validate(df)
                print("✅ Validación exitosa.")
            except SchemaError as e:
                print(f"❌ Error de validación de datos para {symbol}: {e}")
                continue

            filename = f"{symbol}_news.parquet"
            local_path = os.path.join(output_dir, filename)
            df_validated.to_parquet(local_path, index=False)
            
            date_folder = datetime.now().strftime("%Y-%m-%d")
            gcs_path = f"raw/news/{date_folder}/{filename}"
            upload_to_gcs(local_path, gcs_path)
            
        else:
            print(f"⚠️ No se encontraron noticias recientes para {symbol}")

if __name__ == "__main__": 
    fetch_news()