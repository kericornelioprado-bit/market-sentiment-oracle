import requests
import pandas as pd
import os
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv # <--- Importamos dotenv

# 1. Cargar variables de entorno
load_dotenv()

# 2. Obtener la Key de manera segura
API_KEY = os.getenv("NEWS_API_KEY")

# Validación de seguridad
if not API_KEY:
    raise ValueError("❌ ERROR CRÍTICO: No se encontró NEWS_API_KEY en el archivo .env")

# --- CONFIGURACIÓN ---
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
OUTPUT_DIR = "data/raw/news"
FROM_DATE = (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')

def fetch_news():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"--- Descargando Noticias desde {FROM_DATE} ---")

    for ticker in TICKERS:
        print(f"📡 Buscando noticias para: {ticker}...")
        
        url = (f'https://newsapi.org/v2/everything?'
               f'q={ticker}&'
               f'from={FROM_DATE}&'
               f'sortBy=popularity&'
               f'language=en&'
               f'apiKey={API_KEY}') # Usamos la variable cargada
        
        try:
            response = requests.get(url)
            response.raise_for_status() # Lanza error si no es 200 OK
            
            data = response.json()
            articles = data.get('articles', [])
            
            if not articles:
                print(f"⚠️ No se encontraron noticias para {ticker}")
                continue

            df = pd.DataFrame(articles)
            
            if not df.empty:
                # Seleccionamos columnas relevantes para el modelo NLP
                cols_to_keep = ['publishedAt', 'title', 'description', 'source', 'url']
                # Aseguramos que existan las columnas antes de filtrar
                existing_cols = [c for c in cols_to_keep if c in df.columns]
                df = df[existing_cols]
                
                # Limpieza de la fuente
                if 'source' in df.columns:
                    df['source'] = df['source'].apply(lambda x: x['name'] if isinstance(x, dict) else x)
                
                filename = f"{OUTPUT_DIR}/{ticker}_news.parquet"
                df.to_parquet(filename)
                print(f"✅ Guardado: {filename} ({len(df)} artículos)")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de red o API para {ticker}: {e}")
        
        time.sleep(1) 

if __name__ == "__main__":
    fetch_news()