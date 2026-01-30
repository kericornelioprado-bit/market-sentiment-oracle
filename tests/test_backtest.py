
import backtrader as bt
import pandas as pd
import pytest
from unittest.mock import MagicMock
import io
import sys

# --- Módulo a Probar ---
# Importamos la estrategia original para modificarla en nuestro entorno de prueba
from src.backtesting.strategy import MLStrategy

# --- Clases de Prueba y Mocks ---

class TestStrategy(MLStrategy):
    """
    Una versión modificada de la estrategia que usa un modelo mockeado
    para poder controlar las señales de compra/venta durante las pruebas.
    """
    def __init__(self):
        super().__init__()
        # El modelo mock se inyectará directamente en la instancia de la estrategia
        self.model = self.p.model
    
    def next(self):
        if self.order:
            return

        # Simulación de predicción del modelo
        # En lugar de calcular features, usamos un valor predecibilido del mock
        # Creamos un array dummy que simula los datos de entrada para el `predict`
        dummy_input = [[self.dataclose[0]]] # Usamos un valor simple
        signal = self.model.predict(dummy_input)[0]

        if not self.position:
            # Si la señal es > 0.5 (subirá), compramos
            if signal > 0.5:
                self.log(f'SEÑAL DE COMPRA (mocked): {signal:.2f}')
                self.order = self.buy()
        else:
            # Si la señal es <= 0.5 (bajará), vendemos
            if signal <= 0.5:
                self.log(f'SEÑAL DE VENTA (mocked): {signal:.2f}')
                self.order = self.sell()

class MockFeed(bt.feeds.PandasData):
    """
    Un feed de datos personalizado para inyectar datos predecibles en el backtest.
    Hereda de PandasData pero lo alimentamos con nuestro propio DataFrame.
    """
    @classmethod
    def from_dataframe(cls, df):
        return cls(dataname=df)

# --- Pruebas ---

def run_test_scenario(data, mock_model_predictions, initial_cash=10000.0):
    """
    Función de ayuda para ejecutar un escenario de backtesting.
    """
    cerebro = bt.Cerebro()
    
    # 1. Añadir datos
    feed = MockFeed.from_dataframe(data)
    cerebro.adddata(feed)

    # 2. Configurar y añadir estrategia con el modelo mockeado
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_model_predictions
    cerebro.addstrategy(TestStrategy, model=mock_model)
    
    # 3. Configurar broker
    cerebro.broker.setcash(initial_cash)
    
    # 4. Capturar logs (salida estándar)
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    # 5. Ejecutar
    cerebro.run()
    
    # 6. Restaurar salida estándar y devolver resultados
    sys.stdout = old_stdout
    final_value = cerebro.broker.getvalue()
    logs = captured_output.getvalue()
    
    return final_value, logs

def test_buy_signal_creates_buy_order():
    """
    Caso A: El modelo predice una subida, se debe generar una orden de compra.
    """
    # Datos: 5 días con precios al alza
    price_data = pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105],
        'low': [99, 100, 101, 102, 103],
        'close': [101, 102, 103, 104, 105],
        'volume': [1000] * 5
    }, index=pd.to_datetime(pd.date_range(start='2024-01-01', periods=5)))
    
    # Predicciones del modelo: Siempre "subirá" (1)
    predictions = [[1]] * 5
    
    _, logs = run_test_scenario(price_data, predictions)
    
    # Verificación: ¿Se generó la señal de compra y se ejecutó la orden?
    assert "SEÑAL DE COMPRA (mocked): 1.00" in logs
    assert "COMPRA EJECUTADA" in logs

def test_sell_signal_creates_sell_order():
    """
    Caso B: El modelo predice una bajada, se debe generar una orden de venta.
    """
    # Datos: 5 días, primero sube (para comprar) y luego baja
    price_data = pd.DataFrame({
        'open': [100, 102, 101, 100, 99],
        'high': [101, 103, 102, 101, 100],
        'low': [99, 101, 100, 99, 98],
        'close': [101, 102, 100, 99, 98],
        'volume': [1000] * 5
    }, index=pd.to_datetime(pd.date_range(start='2024-01-01', periods=5)))
    
    # Predicciones: El primer día sube (para entrar en posición), luego baja (para vender)
    predictions = [[1], [0], [0], [0], [0]]
    
    _, logs = run_test_scenario(price_data, predictions)
    
    # Verificación: ¿Se generó la señal de venta y se ejecutó la orden?
    assert "SEÑAL DE VENTA (mocked): 0.00" in logs
    assert "VENTA EJECUTADA" in logs

def test_notify_order_logs_execution():
    """
    Verifica que `notify_order` registra la ejecución de una compra.
    Este test es redundante con los anteriores, pero es una buena práctica tenerlo
    explícitamente si la lógica de notificación fuera más compleja.
    """
    price_data = pd.DataFrame({
        'close': [100, 101, 102, 103, 104]
    }, index=pd.to_datetime(pd.date_range(start='2024-01-01', periods=5)))
    price_data['open'] = price_data['high'] = price_data['low'] = price_data['volume'] = price_data['close']

    predictions = [[1]] * 5
    
    _, logs = run_test_scenario(price_data, predictions)
    
    # Verificación del formato del log de ejecución
    assert "COMPRA EJECUTADA, Precio: 101.00, Costo:" in logs
