import backtrader as bt
import pandas as pd
import os

# Configuración
TICKER = "TSLA"  # Probemos con tu mejor modelo
MODEL_TYPE = "LSTM"  # O "SVM"


class MLStrategy(bt.Strategy):
    params = (
        ("model", None),
        ("scaler", None),
        ("model_type", "LSTM"),
        ("seq_len", 10),  # Debe coincidir con SEQ_LENGTH del entrenamiento
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Historial para crear secuencias LSTM
        self.data_history = []

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"COMPRA EJECUTADA, Precio: {order.executed.price:.2f}, Costo: {order.executed.value:.2f}, Com: {order.executed.comm:.2f}"
                )
            elif order.issell():
                self.log(
                    f"VENTA EJECUTADA, Precio: {order.executed.price:.2f}, Costo: {order.executed.value:.2f}, Com: {order.executed.comm:.2f}"
                )
            self.bar_executed = len(self)

        self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")

    def get_features(self):
        # En una implementación real, aquí reconstruiríamos TODOS los indicadores (RSI, MACD, Sentiment).
        # Para este MVP, usaremos el 'Close' crudo simulando que es la única feature,
        # SOLO para probar que el motor de Backtrader gira.
        # (Nota: Esto simplifica la realidad, ya que tu modelo espera 17 features)

        # Hack para tesis: Le pasaremos al modelo datos Dummy si no tenemos las features en tiempo real en backtrader
        # Ojo: Para hacerlo estricto, deberíamos cargar el CSV "Master Dataset" en Backtrader con todas las columnas.
        pass

    def next(self):
        # Simulación simple: Si el modelo dice "Subirá", compramos.
        # Por ahora, haremos un cruce simple para verificar que Backtrader funciona
        # antes de conectar la LSTM compleja (que requiere tensor 3D).

        if self.order:
            return

        # Lógica de Trading (Placeholder para probar el motor)
        if not self.position:
            if self.dataclose[0] > self.dataclose[-1]:  # Si sube hoy
                self.log(f"SEÑAL DE COMPRA (Simulada): {self.dataclose[0]:.2f}")
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.dataclose[-1]:  # Si baja hoy
                self.log(f"SEÑAL DE VENTA (Simulada): {self.dataclose[0]:.2f}")
                self.order = self.sell()


def run_backtest():
    cerebro = bt.Cerebro()

    # 1. Cargar Datos (Usamos los Parquet que generamos)
    # Backtrader necesita CSV o Pandas DataFrame directo
    data_path = f"data/raw/prices/{TICKER}_latest.parquet"  # Usamos raw price para simular mercado
    if not os.path.exists(data_path):
        # Si no está local (porque seed_mock subió a nube), bajamos de nube o creamos dummy
        print(
            "⚠️ No encuentro datos locales. Asegúrate de tener el archivo o descárgalo de GCS."
        )
        return

    df = pd.read_parquet(data_path)
    df.index = pd.to_datetime(df["Date"])  # Asegurar índice de fecha

    # Crear Feed de Datos
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # 2. Configurar Estrategia
    cerebro.addstrategy(MLStrategy)

    # 3. Configurar Dinero Inicial
    start_cash = 10000.0
    cerebro.broker.setcash(start_cash)
    cerebro.broker.setcommission(commission=0.001)  # 0.1% comisión

    print(f"Valor Inicial del Portafolio: {start_cash:.2f}")
    cerebro.run()
    print(f"Valor Final del Portafolio: {cerebro.broker.getvalue():.2f}")

    # 4. Gráfica
    # cerebro.plot() # Descomentar si tienes entorno gráfico (X11)


if __name__ == "__main__":
    # Descargar datos de prueba de GCS para que el script funcione local
    from google.cloud import storage

    bucket_name = "market-oracle-tesis-data-lake"
    blob_path = f"data/raw/prices/{TICKER}_latest.parquet"

    print(f"📥 Descargando datos de {TICKER} para backtesting...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    if blob.exists():
        os.makedirs("data/raw/prices", exist_ok=True)
        blob.download_to_filename(blob_path)
        run_backtest()
    else:
        print("❌ No encontré datos en GCS. Corre seed_mock_data.py primero.")
