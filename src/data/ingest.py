import yfinance as yf
import os
from datetime import datetime, timedelta

# Configuración
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
START_DATE = (datetime.now() - timedelta(days=5 * 365)).strftime(
    "%Y-%m-%d"
)  # Últimos 5 años
END_DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = "data/raw"


def download_market_data():
    """Descarga datos OHLCV de Yahoo Finance y los guarda en Parquet."""

    # Asegurar que existe el directorio
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"--- Iniciando Ingesta: {START_DATE} a {END_DATE} ---")

    # Optimization: Download all tickers in a single batch request
    # This leverages yfinance's threading and reduces HTTP overhead significantly (>10x speedup)
    # group_by='ticker' ensures the returned DataFrame has a MultiIndex with Ticker at the top level
    print(f"Descargando datos para: {TICKERS}")
    try:
        df_all = yf.download(TICKERS, start=START_DATE, end=END_DATE, group_by='ticker', progress=False)
    except Exception as e:
        print(f"❌ Error descargando datos masivos: {e}")
        return

    for ticker in TICKERS:
        try:
            # Extract data for specific ticker
            # This returns a DataFrame with Single Level columns (Open, High, Low, Close, Volume)
            df = df_all[ticker]

            # Remove rows where all columns are NaN (dates where this ticker didn't trade but others did)
            # This restores the dense format of the original sequential download
            df = df.dropna(how='all')

            # Check if data is empty
            if df.empty:
                print(f"⚠️ Alerta: No se encontraron datos para {ticker}")
                continue

            # Guardar en formato Parquet (más eficiente que CSV)
            # Nombre de archivo: AAPL_2026-01-26.parquet
            filename = f"{OUTPUT_DIR}/{ticker}_{END_DATE}.parquet"
            df.to_parquet(filename)
            print(f"✅ Guardado: {filename} ({len(df)} filas)")

        except Exception as e:
            print(f"❌ Error procesando {ticker}: {e}")


if __name__ == "__main__":
    download_market_data()
