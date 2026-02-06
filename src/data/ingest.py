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

    print(f"Descargando batch: {', '.join(TICKERS)}...")

    try:
        # Optimization: Batch download is significantly faster (1 request vs N requests)
        # group_by='ticker' ensures we get a MultiIndex (Ticker, Price)
        batch_data = yf.download(
            TICKERS, start=START_DATE, end=END_DATE, group_by="ticker", progress=False
        )
    except Exception as e:
        print(f"❌ Error fatal descargando batch: {e}")
        return

    for ticker in TICKERS:
        try:
            # Extract ticker dataframe
            # Handle case where yfinance returns a flat DF (single ticker) or MultiIndex (multiple)
            if len(TICKERS) == 1:
                df = batch_data
            else:
                if ticker not in batch_data.columns:
                    print(f"⚠️ Alerta: No se encontraron datos para {ticker} en el batch")
                    continue
                df = batch_data[ticker]

            # Clean empty rows (caused by alignment across different trading histories)
            df = df.dropna(how="all")

            if df.empty:
                print(f"⚠️ Alerta: DataFrame vacío tras limpieza para {ticker}")
                continue

            # Guardar en formato Parquet (más eficiente que CSV)
            filename = f"{OUTPUT_DIR}/{ticker}_{END_DATE}.parquet"
            df.to_parquet(filename)
            print(f"✅ Guardado: {filename} ({len(df)} filas)")

        except Exception as e:
            print(f"❌ Error procesando {ticker}: {e}")


if __name__ == "__main__":
    download_market_data()
