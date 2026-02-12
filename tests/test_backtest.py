import backtrader as bt
import pandas as pd
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
import io
import sys

# --- Módulo a Probar ---
from src.backtesting.strategy import MLStrategy

# --- Clases de Prueba y Mocks ---


class MockStrategy(MLStrategy):
    """
    Una versión modificada de la estrategia que usa un modelo mockeado
    para poder controlar las señales de compra/venta durante las pruebas.
    """

    def start(self):
        """Inicializa el modelo al iniciar la estrategia."""
        self.model = self.p.model

    def next(self):
        if self.order:
            return

        dummy_input = [[self.dataclose[0]]]
        signal = self.model.predict(dummy_input)[0]

        if not self.position:
            if signal > 0.5:
                self.log(f"SEÑAL DE COMPRA (mocked): {signal:.2f}")
                self.order = self.buy()
        else:
            if signal <= 0.5:
                self.log(f"SEÑAL DE VENTA (mocked): {signal:.2f}")
                self.order = self.sell()


class MockFeed(bt.feeds.PandasData):
    """
    Un feed de datos personalizado para inyectar datos predecibles en el backtest.
    """

    @classmethod
    def from_dataframe(cls, df):
        return cls(dataname=df)


# --- Pruebas ---


def run_test_scenario(data, mock_model_predictions, initial_cash=10000.0):
    """
    Función de ayuda para ejecutar un escenario de backtesting con una estrategia mockeada.
    """
    cerebro = bt.Cerebro()
    feed = MockFeed.from_dataframe(data)
    cerebro.adddata(feed)

    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_model_predictions
    cerebro.addstrategy(MockStrategy, model=mock_model)

    cerebro.broker.setcash(initial_cash)

    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    cerebro.run()

    sys.stdout = old_stdout
    logs = captured_output.getvalue()

    return cerebro.broker.getvalue(), logs


def test_buy_signal_creates_buy_order():
    """
    Caso A: El modelo mockeado predice una subida, se debe generar una orden de compra.
    """
    price_data = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [101, 102, 103, 104, 105],
            "volume": [1000] * 5,
        },
        index=pd.to_datetime(pd.date_range(start="2024-01-01", periods=5)),
    )

    predictions = [[1]] * 5

    _, logs = run_test_scenario(price_data, predictions)

    assert "SEÑAL DE COMPRA (mocked): 1.00" in logs
    assert "COMPRA EJECUTADA" in logs


def test_sell_signal_creates_sell_order():
    """
    Caso B: El modelo mockeado predice una bajada, se debe generar una orden de venta.
    """
    price_data = pd.DataFrame(
        {
            "open": [100, 102, 101, 100, 99],
            "high": [101, 103, 102, 101, 100],
            "low": [99, 101, 100, 99, 98],
            "close": [101, 102, 100, 99, 98],
            "volume": [1000] * 5,
        },
        index=pd.to_datetime(pd.date_range(start="2024-01-01", periods=5)),
    )

    predictions = [[1], [0], [0], [0], [0]]

    _, logs = run_test_scenario(price_data, predictions)

    assert "SEÑAL DE VENTA (mocked): 0.00" in logs
    assert "VENTA EJECUTADA" in logs


def test_ml_strategy_triggers_orders_on_crossover():
    """
    Test para la MLStrategy original, verificando que la lógica
    de trading real (cruce de medias) genera órdenes de compra y venta.
    """
    # 1. Crear Data Feed sintético con tendencias claras
    n_days = 80
    date_range = pd.to_datetime(pd.date_range(start="2024-01-01", periods=n_days))

    # Días 0-20: Precio bajo y estable
    p1 = np.full(21, 100.0)
    # Días 21-50: Subida agresiva a 200
    p2 = np.linspace(100, 200, 30)
    # Días 51-79: Caída agresiva a 50
    p3 = np.linspace(200, 50, 29)

    close_prices = np.concatenate([p1, p2, p3])

    price_data = pd.DataFrame(
        {
            "open": close_prices - 1,
            "high": close_prices + 1,
            "low": close_prices - 1,
            "close": close_prices,
            "volume": [1000] * n_days,
        },
        index=date_range,
    )

    # 2. Configurar y ejecutar Cerebro con la estrategia real
    cerebro = bt.Cerebro()
    feed = MockFeed.from_dataframe(price_data)
    cerebro.adddata(feed)
    cerebro.addstrategy(MLStrategy)  # Usamos la estrategia original
    cerebro.broker.setcash(10000.0)

    # Capturar logs
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()

    # 3. Ejecutar
    strategies = cerebro.run()
    strategy_instance = strategies[0]

    sys.stdout = old_stdout
    logs = captured_output.getvalue()

    # 4. Aserciones
    # Verificar que se generaron señales de compra y venta en los logs
    assert "SEÑAL DE COMPRA (Simulada)" in logs
    assert "COMPRA EJECUTADA" in logs
    assert "SEÑAL DE VENTA (Simulada)" in logs
    assert "VENTA EJECUTADA" in logs

    # Verificar que la estrategia tiene un registro de órdenes
    assert hasattr(strategy_instance, "order")

def test_ml_strategy_hold_scenarios():
    """
    Test cases where no order is placed:
    1. Signal > 0.5 but already in position (Hold).
    2. Signal <= 0.5 but not in position (Wait).
    """
    # Create simple data
    price_data = pd.DataFrame(
        {
            "open": [100, 100, 100],
            "high": [101, 101, 101],
            "low": [99, 99, 99],
            "close": [100, 100, 100],
            "volume": [1000] * 3,
        },
        index=pd.to_datetime(pd.date_range(start="2024-01-01", periods=3)),
    )
    
    # Case 2: Signal <= 0.5, No Position -> Do nothing
    predictions_sell = [[0.1], [0.1], [0.1]]
    _, logs_sell = run_test_scenario(price_data, predictions_sell)
    assert "SEÑAL DE COMPRA" not in logs_sell
    assert "SEÑAL DE VENTA" not in logs_sell # No position to sell
    
    # To test Case 1 (Signal > 0.5, Position Exists), we need to simulate having a position.
    # We can do this by first sending a Buy signal, then another Buy signal.
    predictions_buy_twice = [[0.8], [0.8], [0.8]]
    _, logs_buy = run_test_scenario(price_data, predictions_buy_twice)
    
    # Should see "SEÑAL DE COMPRA" for the first one
    # But checking if we see duplicate orders is harder via logs unless we parse "Order ref"
    # But MockStrategy code:
    # if self.order: return (Pending order)
    # if not self.position: buy
    # else: if signal <= 0.5: sell
    # So if position exists and signal > 0.5, it does nothing (which is explicitly ELSE of "signal <= 0.5" check implies continue)
    
    assert logs_buy.count("SEÑAL DE COMPRA") >= 1 # At least one
    # Note: MockStrategy logs "SEÑAL DE COMPRA" irrespective of position? 
    # No:
    # if not self.position:
    #    if signal > 0.5: log... buy...
    # else:
    #    ...
    # So if in position, it goes to else.
    # In else, if signal <= 0.5, it sells.
    # If signal > 0.5 in else branch, it does NOTHING.
    # So "SEÑAL DE COMPRA" should appear ONLY ONCE (when entering).
    
    assert logs_buy.count("SEÑAL DE COMPRA") == 1

@patch("src.backtesting.strategy.bt.Cerebro")
@patch("src.backtesting.strategy.pd.read_parquet")
@patch("src.backtesting.strategy.os.path.exists")
def test_run_backtest_function(mock_exists, mock_read_parquet, mock_cerebro):
    from src.backtesting.strategy import run_backtest
    
    # Mock data existence
    mock_exists.return_value = True
    
    # Mock dataframe
    df = pd.DataFrame({"Close": [100.0], "Date": ["2023-01-01"]})
    mock_read_parquet.return_value = df
    
    # Mock Cerebro
    mock_instance = MagicMock()
    mock_cerebro.return_value = mock_instance
    mock_instance.broker.getvalue.return_value = 10000.0
    
    run_backtest()
    
    assert mock_instance.run.called
    assert mock_instance.addstrategy.called
    assert mock_instance.adddata.called

