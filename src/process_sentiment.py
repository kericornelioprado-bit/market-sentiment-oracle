import os
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from google.cloud import storage
import io

# Configuración
BUCKET_NAME = "market-oracle-tesis-data-lake"  # Tu bucket creado en Fase 1 [cite: 240]
MODEL_NAME = "ProsusAI/finbert" # Modelo FinBERT estándar [cite: 83]

def load_model():
    """Carga el modelo y tokenizador de Hugging Face."""
    print(f"🔄 Cargando modelo {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    return tokenizer, model

def get_sentiment(text, tokenizer, model):
    """
    Convierte texto en sentimiento usando FinBERT.
    Retorna: Etiqueta (positive, negative, neutral) y Score.
    """
    if not isinstance(text, str) or not text.strip():
        return "neutral", 0.0

    # Tokenizar
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    
    # Inferencia (sin gradientes para ahorrar memoria)
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Convertir logits a probabilidades
    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    # Obtener la clase con mayor probabilidad
    positive = predictions[:, 0].item()
    negative = predictions[:, 1].item()
    neutral = predictions[:, 2].item()
    
    # Lógica simple de FinBERT (ProsusAI output: 0=Positive, 1=Negative, 2=Neutral)
    # Nota: Verificar el config del modelo específico, a veces varía.
    # Para ProsusAI suele ser: [positive, negative, neutral]
    
    labels = ["positive", "negative", "neutral"]
    scores = [positive, negative, neutral]
    
    max_score_idx = scores.index(max(scores))
    return labels[max_score_idx], scores[max_score_idx]

def process_bucket_files():
    """Recorre el bucket, procesa archivos raw y guarda los procesados."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    
    # Cargar IA una sola vez
    tokenizer, model = load_model()
    
    # Listar archivos en la carpeta raw (ingesta diaria)
    blobs = bucket.list_blobs(prefix="data/raw/")
    
    for blob in blobs:
        if not blob.name.endswith(".parquet"):
            continue
            
        print(f"📄 Procesando: {blob.name}")
        
        # Leer desde GCS sin bajar al disco duro [cite: 73]
        data = blob.download_as_bytes()
        df = pd.read_parquet(io.BytesIO(data))
        
        if "title" not in df.columns:
            print(f"⚠️ Saltando {blob.name}: No tiene columna 'title'")
            continue
            
        # --- APLICAR IA ---
        # Usamos apply para procesar cada fila. 
        # En producción masiva usaríamos batching, pero para tesis esto funciona.
        print("   🧠 Analizando sentimientos...")
        
        # Analizamos el título (suele ser más denso en información que el description)
        df[["sentiment_label", "sentiment_score"]] = df["title"].apply(
            lambda x: pd.Series(get_sentiment(x, tokenizer, model))
        )
        
        # --- GUARDAR ---
        # Definir nueva ruta: data/processed/embeddings/...
        new_blob_name = blob.name.replace("data/raw/", "data/processed/embeddings/")
        
        # Convertir a Parquet en memoria
        output_buffer = io.BytesIO()
        df.to_parquet(output_buffer, index=False)
        
        # Subir a GCS
        new_blob = bucket.blob(new_blob_name)
        new_blob.upload_from_file(output_buffer, rewind=True)
        print(f"✅ Guardado en: {new_blob_name}")

if __name__ == "__main__":
    print("🚀 Iniciando Pipeline de Procesamiento NLP")
    process_bucket_files()