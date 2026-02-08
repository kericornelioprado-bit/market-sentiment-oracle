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

    try:
        # Optimization: Use batch download for parallel processing (~4x faster)
        # group_by='ticker' ensures the result is a MultiIndex with (Ticker, PriceType)
        print(f"Descargando {len(TICKERS)} tickers en batch...")
        df_all = yf.download(TICKERS, start=START_DATE, end=END_DATE, progress=False, group_by='ticker')

        if df_all.empty:
             print("⚠️ Alerta: La descarga masiva no retornó datos.")
             return

        is_multiindex = isinstance(df_all.columns, pd.MultiIndex)

        for ticker in TICKERS:
            try:
                if is_multiindex:
                    if ticker in df_all.columns:
                        df = df_all[ticker]
                    else:
                        print(f"⚠️ Alerta: No se encontraron datos para {ticker} en el batch.")
                        continue
                else:
                    # If not MultiIndex, it implies single ticker result or flat structure.
                    # If we requested multiple tickers but got flat structure, it might be an issue,
                    # but if we requested 1 ticker, this is expected.
                    df = df_all

                # Limpieza: eliminar filas vacías (días sin trading para este ticker)
                df = df.dropna(how='all')

                if df.empty:
                    print(f"⚠️ Alerta: No se encontraron datos válidos para {ticker}")
                    continue

                # Guardar en formato Parquet (más eficiente que CSV)
                # Nombre de archivo: AAPL_2026-01-26.parquet
                filename = f"{OUTPUT_DIR}/{ticker}_{END_DATE}.parquet"
                df.to_parquet(filename)
                print(f"✅ Guardado: {filename} ({len(df)} filas)")

            except Exception as e:
                print(f"❌ Error procesando {ticker}: {e}")

    except Exception as e:
        print(f"❌ Error en descarga masiva: {e}")


if __name__ == "__main__":
    download_market_data()
