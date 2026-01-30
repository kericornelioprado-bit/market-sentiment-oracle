import pandas as pd
import numpy as np
from datetime import datetime
from google.cloud import storage
import io
import os

# Importamos tu nuevo módulo de indicadores
from src.features.technical_indicators import add_technical_features

class DataMerger:
    def __init__(self, bucket_name: str, tickers: list):
        self.bucket_name = bucket_name
        self.tickers = tickers
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

    def load_parquet_from_gcs(self, blob_name: str) -> pd.DataFrame:
        """Descarga un parquet de GCS directamente a DataFrame."""
        blob = self.bucket.blob(blob_name)
        if not blob.exists():
            print(f"⚠️ Alerta: No se encontró {blob_name}")
            return pd.DataFrame()
        
        data = blob.download_as_bytes()
        return pd.read_parquet(io.BytesIO(data))

    def process_sentiment_aggregation(self, df_sentiment: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte el stream de noticias intradía en una señal diaria unificada.
        Estrategia: Promedio ponderado por confianza (Score).
        """
        if df_sentiment.empty:
            return pd.DataFrame()

        # 1. Mapeo de etiquetas a valores numéricos
        # Positive = 1, Negative = -1, Neutral = 0
        label_map = {'positive': 1, 'negative': -1, 'neutral': 0}
        
        # Validar que las columnas existan (defensa contra esquemas rotos)
        if 'sentiment_label' not in df_sentiment.columns:
            return pd.DataFrame()

        df_sentiment['numeric_label'] = df_sentiment['sentiment_label'].map(label_map)
        
        # 2. Sentimiento Ponderado = Valor (-1 a 1) * Confianza (0 a 1)
        # Una noticia muy negativa con alta confianza pesará cerca de -1.
        df_sentiment['weighted_score'] = df_sentiment['numeric_label'] * df_sentiment['sentiment_score']

        # 3. Asegurar fechas (ignorar horas para agrupar por día)
        # Asumimos que hay una columna 'date' o 'publishedAt'
        date_col = 'date' if 'date' in df_sentiment.columns else 'publishedAt'
        df_sentiment['date_only'] = pd.to_datetime(df_sentiment[date_col]).dt.normalize()

        # 4. Agregación: GroupBy fecha
        # Calculamos:
        # - mean_sentiment: El sentimiento promedio del día
        # - news_count: Volumen de noticias (volatilidad de atención)
        daily_sentiment = df_sentiment.groupby('date_only').agg(
            daily_sentiment=('weighted_score', 'mean'),
            news_volume=('weighted_score', 'count')
        ).reset_index()

        return daily_sentiment

    def run_pipeline(self):
        print(f"🚀 Iniciando fusión de datos para: {self.tickers}")
        
        for ticker in self.tickers:
            print(f"\n--- Procesando {ticker} ---")
            
            # 1. Cargar Precios (Raw)
            # Ajusta la ruta según cómo guardaste en ingesta (raw/prices/TICKER/...)
            # Aquí buscaremos el archivo consolidado o iteraremos. 
            # Para simplificar, asumiremos que existe un consolidado o tomamos el más reciente.
            prices_blob = f"data/raw/prices/{ticker}_latest.parquet" 
            df_price = self.load_parquet_from_gcs(prices_blob)
            
            if df_price.empty:
                print(f"❌ No hay precios para {ticker}, saltando.")
                continue

            # Limpieza básica de precios
            df_price['Date'] = pd.to_datetime(df_price['Date']).dt.normalize()
            df_price.set_index('Date', inplace=True)
            df_price.sort_index(inplace=True)

            # 2. Calcular Indicadores Técnicos (Usando tu módulo)
            print("   📊 Calculando RSI, MACD, Bollinger...")
            df_price = add_technical_features(df_price, price_col='Close')

            # 3. Cargar Sentimiento (Processed)
            sentiment_blob = f"data/processed/embeddings/{ticker}_sentiment.parquet"
            df_sentiment = self.load_parquet_from_gcs(sentiment_blob)
            
            if not df_sentiment.empty:
                print("   🧠 Agregando señales de sentimiento...")
                daily_sentiment = self.process_sentiment_aggregation(df_sentiment)
                
                # 4. MERGE (Left Join usando el índice de precios)
                # Usamos left join para mantener todos los días de trading, 
                # aunque no haya noticias.
                daily_sentiment.set_index('date_only', inplace=True)
                master_df = df_price.join(daily_sentiment, how='left')
                
                # 5. Manejo de NaNs en Sentimiento
                # Si no hubo noticias ese día, el sentimiento es Neutral (0)
                master_df['daily_sentiment'] = master_df['daily_sentiment'].fillna(0)
                master_df['news_volume'] = master_df['news_volume'].fillna(0)
                
            else:
                print("⚠️ No se encontraron noticias procesadas. Llenando con ceros.")
                master_df = df_price
                master_df['daily_sentiment'] = 0
                master_df['news_volume'] = 0

            # 6. Guardar Dataset Maestro (Feature Matrix)
            # Eliminamos filas con NaNs generados por los indicadores técnicos (los primeros 20-30 días)
            master_df.dropna(inplace=True)
            
            output_path = f"data/gold/master_dataset_{ticker}.parquet"
            # Guardar en buffer y subir
            buff = io.BytesIO()
            master_df.to_parquet(buff)
            buff.seek(0)
            
            self.bucket.blob(output_path).upload_from_file(buff)
            print(f"✅ Dataset Maestro guardado en: gs://{self.bucket_name}/{output_path}")
            print(f"   Shape final: {master_df.shape}")

if __name__ == "__main__":
    # Configuración
    BUCKET_NAME = "market-oracle-tesis-data-lake" # Ajusta a tu nombre real
    TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
    
    merger = DataMerger(BUCKET_NAME, TICKERS)
    merger.run_pipeline()