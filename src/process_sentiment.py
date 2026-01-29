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

def get_sentiment_batch(texts, tokenizer, model, batch_size=32):
    """
    Convierte una lista de textos en sentimientos usando FinBERT por lotes.
    Retorna: Lista de tuplas (etiqueta, score).
    Optimizado para evitar overhead de llamadas individuales.
    """
    results = []

    # Procesar en lotes
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]

        # Identificar textos validos para inferencia
        valid_indices = []
        valid_texts = []
        # Inicializar resultados con neutral por defecto para textos vacios
        batch_results = [("neutral", 0.0)] * len(batch_texts)

        for idx, text in enumerate(batch_texts):
            if isinstance(text, str) and text.strip():
                valid_indices.append(idx)
                valid_texts.append(text)

        # Si no hay textos validos en el lote, continuar
        if not valid_texts:
            results.extend(batch_results)
            continue

        # Tokenizar solo los validos
        inputs = tokenizer(valid_texts, return_tensors="pt", truncation=True, padding=True, max_length=512)

        # Mover a device del modelo (GPU/CPU)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # Inferencia
        with torch.no_grad():
            outputs = model(**inputs)

        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # Mapping labels
        labels_map = ["positive", "negative", "neutral"]

        for j, probs in enumerate(predictions):
            scores = probs.tolist()
            max_score = max(scores)
            max_idx = scores.index(max_score)

            # Asignar resultado a la posicion original
            original_idx = valid_indices[j]
            batch_results[original_idx] = (labels_map[max_idx], max_score)

        results.extend(batch_results)

    return results

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
        print("   🧠 Analizando sentimientos por lotes...")
        titles = df["title"].tolist()
        batch_results = get_sentiment_batch(titles, tokenizer, model, batch_size=32)

        df_results = pd.DataFrame(batch_results, columns=["sentiment_label", "sentiment_score"])
        # Usar .values para evitar problemas de alineacion de indices si df esta filtrado
        df["sentiment_label"] = df_results["sentiment_label"].values
        df["sentiment_score"] = df_results["sentiment_score"].values
        
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