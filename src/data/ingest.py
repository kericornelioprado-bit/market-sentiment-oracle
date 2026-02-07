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

    print(f"Descargando datos para {len(TICKERS)} tickers...")
    try:
        # Optimización: Descarga en lote (Batch Download)
        # group_by='ticker' asegura que el nivel superior de las columnas sea el Ticker.
        # Esto reduce significativamente el tiempo de descarga (aprox 4x más rápido).
        data = yf.download(TICKERS, start=START_DATE, end=END_DATE, progress=False, group_by='ticker')

        if data.empty:
            print(f"⚠️ Alerta: No se encontraron datos para ningun ticker")
            return

        for ticker in TICKERS:
            try:
                # Extraer datos del ticker específico
                # Si data es MultiIndex (Ticker, Price), data[ticker] devuelve DataFrame con columnas Price (Open, High, etc)
                df = data[ticker].copy()
            except KeyError:
                print(f"⚠️ Alerta: No se encontraron datos para {ticker} en la respuesta batch")
                continue

            # Eliminar filas vacías (días donde este ticker no operó pero otros sí)
            # Esto es crucial en batch downloads porque el índice es la unión de todas las fechas.
            df.dropna(how='all', inplace=True)

            if df.empty:
                print(f"⚠️ Alerta: DataFrame vacio para {ticker} tras limpieza")
                continue

            # Guardar en formato Parquet (más eficiente que CSV)
            # Nombre de archivo: AAPL_2026-01-26.parquet
            filename = f"{OUTPUT_DIR}/{ticker}_{END_DATE}.parquet"
            df.to_parquet(filename)
            print(f"✅ Guardado: {filename} ({len(df)} filas)")

    except Exception as e:
        print(f"❌ Error descargando batch: {e}")


if __name__ == "__main__":
    download_market_data()
