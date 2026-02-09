import yfinance as yf
import pandas as pd
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
    print(f"Descargando datos para {len(TICKERS)} tickers...")

    try:
        # Descargar datos en batch
        # Optimization: Batch download is ~10x faster than sequential
        data = yf.download(TICKERS, start=START_DATE, end=END_DATE, group_by='ticker', progress=False)

        if data.empty:
            print("⚠️ Alerta: No se encontraron datos para ningun ticker")
            return

        is_multiindex = isinstance(data.columns, pd.MultiIndex)

        for ticker in TICKERS:
            df = pd.DataFrame()

            if is_multiindex:
                try:
                    # Extract data for specific ticker
                    df = data[ticker].copy()
                except KeyError:
                    print(f"⚠️ Alerta: No se encontraron datos para {ticker}")
                    continue
            else:
                # Handle case where single ticker might return simple DataFrame
                if len(TICKERS) == 1 and TICKERS[0] == ticker:
                    df = data.copy()
                else:
                    continue

            # Drop rows where all columns are NaN (e.g. trading holidays specific to other tickers)
            df.dropna(how='all', inplace=True)

            if df.empty:
                print(f"⚠️ Alerta: No se encontraron datos validos para {ticker}")
                continue

            # Guardar en formato Parquet (más eficiente que CSV)
            # Nombre de archivo: AAPL_2026-01-26.parquet
            filename = f"{OUTPUT_DIR}/{ticker}_{END_DATE}.parquet"
            df.to_parquet(filename)
            print(f"✅ Guardado: {filename} ({len(df)} filas)")

    except Exception as e:
        print(f"❌ Error descargando datos: {e}")


if __name__ == "__main__":
    download_market_data()
