
import os
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock, call

# --- Módulos a Probar ---
from src.models.train_svm import SVMTrainer
from src.models.train_lstm import LSTMTrainer

# --- Fixtures ---

@pytest.fixture
def mock_master_dataset():
    """Crea un DataFrame maestro sintético para las pruebas."""
    dates = pd.to_datetime(pd.date_range(start='2024-01-01', periods=100))
    data = {
        'Close': np.random.uniform(100, 200, size=100),
        'Open': np.random.uniform(100, 200, size=100),
        'High': np.random.uniform(100, 200, size=100),
        'Low': np.random.uniform(100, 200, size=100),
        'Volume': np.random.randint(1e6, 5e6, size=100),
        'rsi_14': np.random.uniform(30, 70, size=100),
        'macd_line': np.random.uniform(-1, 1, size=100),
        'daily_sentiment': np.random.uniform(-0.5, 0.5, size=100),
        'news_volume': np.random.randint(0, 10, size=100),
        'Ticker': 'TEST'
    }
    return pd.DataFrame(data, index=dates)

# --- Pruebas para train_lstm.py ---

@pytest.mark.parametrize("input_rows, window_size, expected_sequences", [
    (100, 10, 90),
    (50, 5, 45),
    (20, 10, 10)
])
def test_lstm_create_sequences_shape(input_rows, window_size, expected_sequences):
    """Verifica que la función create_sequences genere el shape correcto."""
    # Forzar uso de CPU
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    
    trainer = LSTMTrainer(bucket_name="dummy")
    X = np.random.rand(input_rows, 5)  # 5 features
    y = np.random.randint(0, 2, size=input_rows)
    
    X_seq, y_seq = trainer.create_sequences(X, y, time_steps=window_size)
    
    assert X_seq.shape == (expected_sequences, window_size, 5)
    assert y_seq.shape == (expected_sequences,)

@patch('src.models.train_lstm.LSTMTrainer.load_data')
@patch('tensorflow.keras.models.Sequential.fit')
@patch('tensorflow.keras.models.Sequential.save')
@patch('joblib.dump')
def test_lstm_train_flow_and_shapes(mock_joblib_dump, mock_model_save, mock_fit, mock_load_data, mock_master_dataset):
    """
    Prueba el flujo de entrenamiento de LSTM:
    1. Mockea la carga de datos.
    2. Mockea el `fit` del modelo.
    3. Verifica que `fit` fue llamado con datos del shape correcto.
    4. Verifica que se llame al guardado del modelo y el scaler.
    """
    # Forzar uso de CPU
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    
    mock_load_data.return_value = mock_master_dataset
    trainer = LSTMTrainer(bucket_name="fake-bucket")
    trainer.train(ticker="TEST")

    # Verificación de `fit`
    assert mock_fit.called
    call_args, _ = mock_fit.call_args
    X_train_arg = call_args[0]
    
    # Después del split 80/20 (80 filas) y la creación de secuencias (80-10=70)
    # El número de features es 9 (Close, Open, High, Low, Volume, rsi, macd, sentiment, volume)
    expected_shape = (70, 10, 9) 
    assert X_train_arg.shape == expected_shape

    # Verificación de guardado
    mock_model_save.assert_called_once_with('models/lstm_TEST.keras')
    mock_joblib_dump.assert_called_once()
    assert mock_joblib_dump.call_args[0][1] == 'models/scaler_lstm_TEST.pkl'

# --- Pruebas para train_svm.py ---

@patch('src.models.train_svm.SVMTrainer.load_data')
@patch('src.models.train_svm.GridSearchCV')
@patch('joblib.dump')
def test_svm_train_flow_and_shapes(mock_joblib_dump, mock_gridsearchcv, mock_load_data, mock_master_dataset):
    """
    Prueba el flujo de entrenamiento de SVM:
    1. Mockea la carga de datos.
    2. Mockea `GridSearchCV` y su `fit`.
    3. Verifica que `fit` fue llamado con los datos correctos.
    4. Verifica que `joblib.dump` es llamado para guardar el modelo y el scaler.
    """
    # Configurar el mock de GridSearchCV para que tenga los atributos necesarios
    mock_grid_instance = MagicMock()
    mock_grid_instance.best_params_ = {}
    mock_grid_instance.best_estimator_ = MagicMock()
    # 20% de 99 filas de test -> 20. El predict debe devolver algo con esa longitud.
    mock_grid_instance.predict.return_value = np.zeros(20)
    mock_gridsearchcv.return_value = mock_grid_instance

    mock_load_data.return_value = mock_master_dataset
    trainer = SVMTrainer(bucket_name="fake-bucket")
    
    trainer.train(ticker="TEST")

    # Verificación de `fit`
    assert mock_grid_instance.fit.called
    call_args, _ = mock_grid_instance.fit.call_args
    X_train_arg = call_args[0]
    
    # 99 filas después de dropear el último NaN del target. 80% de 99 es ~79, pero el slicing produce 80.
    # El número de features para SVM es 4: rsi_14, macd_line, daily_sentiment, news_volume
    expected_rows = 80
    expected_features = 4
    assert X_train_arg.shape == (expected_rows, expected_features)

    # Verificación de guardado
    from unittest.mock import ANY
    assert mock_joblib_dump.call_count == 2
    mock_joblib_dump.assert_any_call(mock_grid_instance.best_estimator_, 'models/svm_TEST.pkl')
    mock_joblib_dump.assert_any_call(ANY, 'models/scaler_TEST.pkl')
