import sys
import json
import numpy as np
import os
import websocket
import logging
import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, QThread, pyqtSignal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Constants
DERIV_API_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"
API_KEY = os.getenv("DERIV_API_KEY")  # Secure API key handling
SYMBOLS = ["frxXAUUSD", "frxEURUSD", "frxGBPUSD", "frxUSDJPY", "cryBTCUSD", "R_75", "R_50", "R_10", "R_100"]
TIMEFRAMES = {"1H": 3600, "30M": 1800, "15M": 900, "5m": 300}  # Timeframes in seconds


class TradingBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Bot")
        self.setGeometry(100, 100, 400, 500)

        self.labels = {}
        layout = QVBoxLayout()

        for symbol in SYMBOLS:
            self.labels[symbol] = {
                "price": QLabel(f"{symbol} Live Price: Loading...", self),
                "signal": QLabel(f"{symbol} Trading Signal: None", self),
                "session": QLabel(f"{symbol} Trading Session: Unknown", self)
            }
            layout.addWidget(self.labels[symbol]["price"])
            layout.addWidget(self.labels[symbol]["signal"])
            layout.addWidget(self.labels[symbol]["session"])

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.ws = websocket.WebSocketApp(DERIV_API_URL,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_open=self.on_open)
        self.start_websocket()

    def start_websocket(self):
        import threading
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

    def on_open(self, ws):
        for symbol in SYMBOLS:
            ws.send(json.dumps({"ticks": symbol}))

    def on_message(self, ws, message):
        data = json.loads(message)
        if "tick" in data:
            symbol = data["tick"]["symbol"]
            price = float(data["tick"]["quote"])
            signal = self.fetch_trading_signal(symbol, price)
            session = self.get_trading_session()

            self.labels[symbol]["price"].setText(f"{symbol} Live Price: {price}")
            self.labels[symbol]["signal"].setText(f"{symbol} Trading Signal: {signal}")
            self.labels[symbol]["session"].setText(f"{symbol} Trading Session: {session}")

    def on_error(self, ws, error):
        logging.error(f"WebSocket Error: {error}")

    def fetch_historical_data(self, symbol, count=14, timeframe=60):
        return []  # Implement real API call here

    def calculate_rsi(self, symbol, period=14, timeframe=60):
        prices = self.fetch_historical_data(symbol, period + 1, timeframe)
        if len(prices) < period + 1:
            return 50

        gains, losses = [], []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period if sum(losses) > 0 else 1e-10
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def detect_liquidity_grab(self, symbol, timeframe=60):
        candles = self.fetch_historical_data(symbol, 10, timeframe)
        if len(candles) < 10:
            return False
        high, low, close = max(candles), min(candles), candles[-1]
        return close > low * 1.01 and close < high * 0.99

    def get_trading_session(self):
        current_hour = datetime.datetime.utcnow().hour
        if 0 <= current_hour < 8:
            return "Asian"
        elif 8 <= current_hour < 16:
            return "London"
        else:
            return "New York"

    def fetch_trading_signal(self, symbol, price):
        final_signal = "Hold"
        confirmations = 0

        for label, timeframe in TIMEFRAMES.items():
            rsi = self.calculate_rsi(symbol, period=14, timeframe=timeframe)
            liquidity_grab = self.detect_liquidity_grab(symbol, timeframe=timeframe)

            if liquidity_grab and rsi < 30:
                confirmations += 1
            elif liquidity_grab and rsi > 70:
                confirmations -= 1

        if confirmations >= 2:
            final_signal = "Strong Buy"
        elif confirmations <= -2:
            final_signal = "Strong Sell"

        return final_signal


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingBotGUI()
    window.show()
    sys.exit(app.exec())
