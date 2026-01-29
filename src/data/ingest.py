import yfinance as yf
import os
from datetime import datetime, timedelta

# Configuración
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
START_DATE = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d') # Últimos 5 años
END_DATE = datetime.now().strftime('%Y-%m-%d')
OUTPUT_DIR = "data/raw"

def download_market_data():
    """Descarga datos OHLCV de Yahoo Finance y los guarda en Parquet."""
    
    # Asegurar que existe el directorio
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"--- Iniciando Ingesta: {START_DATE} a {END_DATE} ---")
    
    for ticker in TICKERS:
        print(f"Descargando {ticker}...")
        try:
            # Descargar datos
            df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
            
            if df.empty:
                print(f"⚠️ Alerta: No se encontraron datos para {ticker}")
                continue
            
            # Guardar en formato Parquet (más eficiente que CSV)
            # Nombre de archivo: AAPL_2026-01-26.parquet
            filename = f"{OUTPUT_DIR}/{ticker}_{END_DATE}.parquet"
            df.to_parquet(filename)
            print(f"✅ Guardado: {filename} ({len(df)} filas)")
            
        except Exception as e:
            print(f"❌ Error descargando {ticker}: {e}")

if __name__ == "__main__":
    download_market_data()