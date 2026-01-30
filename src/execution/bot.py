
import logging
import os

# Intento importar dotenv solo si existe (Entorno Local)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("INFO: Loaded variables from .env file")
except ImportError:
    # Si falla, asumimos que estamos en Kubernetes/Cloud y las vars ya están seteadas
    print("INFO: Running in Cloud mode (dotenv not found), relying on Environment Variables")
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.common.exceptions import APIError

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    """
    A trading bot that interacts with Alpaca Markets to execute trades based on model predictions.
    """
    def __init__(self, paper=True):
        """
        Initializes the TradingBot with API keys from environment variables.
        """
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in environment variables.")
            
        self.client = TradingClient(self.api_key, self.secret_key, paper=paper)
        logging.info("TradingBot initialized successfully with alpaca-py.")

    def check_market_status(self, force_test=False):
        """
        Checks if the market is open. If not, logs a warning and stops unless in test mode.
        """
        try:
            clock = self.client.get_clock()
            if not clock.is_open:
                if force_test:
                    logging.warning("Market is closed, but proceeding in test mode.")
                    return True
                else:
                    logging.warning("Market is closed. Halting execution.")
                    return False
            logging.info("Market is open.")
            return True
        except Exception as e:
            logging.error(f"Error checking market status: {e}")
            return False

    def execute_trade(self, ticker, signal, confidence):
        """
        Executes a trade based on the provided signal and confidence level.
        - signal: "BUY", "SELL", or "HOLD".
        - confidence: A float indicating the model's confidence in the signal.
        """
        if signal == "HOLD":
            logging.info(f"Signal is HOLD for {ticker}. No action taken.")
            return

        if confidence <= 0.75:
            logging.info(f"Confidence for {ticker} ({confidence:.2f}) is below threshold (0.75). No action taken.")
            return

        try:
            if signal == "BUY":
                logging.info(f"Executing BUY for {ticker} with confidence {confidence:.2f}.")
                order_data = MarketOrderRequest(
                    symbol=ticker,
                    notional=10000,  # $10,000 USD fixed allocation
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                )
                self.client.submit_order(order_data=order_data)
                logging.info(f"Market BUY order for $10,000 of {ticker} submitted.")
            
            elif signal == "SELL":
                logging.info(f"Executing SELL for {ticker} with confidence {confidence:.2f}.")
                # Sells the entire position for the given ticker
                try:
                    self.client.close_position(ticker)
                    logging.info(f"Market SELL order to close entire position of {ticker} submitted.")
                except APIError as e:
                    if e.status_code == 404:
                        logging.info(f"No active position for {ticker} to sell.")
                    else:
                        logging.error(f"Failed to close position for {ticker}: {e}")

        except Exception as e:
            logging.error(f"Failed to execute trade for {ticker}: {e}")

if __name__ == "__main__":
    # This block is for demonstration and testing purposes.
    # In a real scenario, you would load predictions from a file or another service.
    
    # --- IMPORTANT ---
    # Make sure to set your Alpaca API keys as environment variables
    # Example for paper trading:
    # export ALPACA_API_KEY='YOUR_PAPER_API_KEY'
    # export ALPACA_SECRET_KEY='YOUR_PAPER_SECRET_KEY'
    
    bot = TradingBot(paper=True)
    
    # Check market status, but force execution for testing if market is closed
    if bot.check_market_status(force_test=True):
        # Simulated prediction for demonstration
        simulated_prediction = {
            "ticker": "AAPL",
            "signal": "BUY",
            "confidence": 0.85
        }
        
        logging.info(f"Processing simulated prediction: {simulated_prediction}")
        
        bot.execute_trade(
            ticker=simulated_prediction["ticker"],
            signal=simulated_prediction["signal"],
            confidence=simulated_prediction["confidence"]
        )
        
        # Example of a SELL signal
        simulated_sell_prediction = {
            "ticker": "MSFT",
            "signal": "SELL",
            "confidence": 0.92
        }
        logging.info(f"Processing simulated prediction: {simulated_sell_prediction}")
        bot.execute_trade(
            ticker=simulated_sell_prediction["ticker"],
            signal=simulated_sell_prediction["signal"],
            confidence=simulated_sell_prediction["confidence"]
        )
        
        # Example of a HOLD signal
        simulated_hold_prediction = {
            "ticker": "GOOGL",
            "signal": "HOLD",
            "confidence": 0.60
        }
        logging.info(f"Processing simulated prediction: {simulated_hold_prediction}")
        bot.execute_trade(
            ticker=simulated_hold_prediction["ticker"],
            signal=simulated_hold_prediction["signal"],
            confidence=simulated_hold_prediction["confidence"]
        )

        logging.info("Simulated trading execution finished.")
