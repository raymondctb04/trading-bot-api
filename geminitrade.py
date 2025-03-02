import tkinter as tk
from tkinter import messagebox
import requests
import random
import datetime
import numpy as np
import websocket
import json

# Constants for ICT concepts
KILL_ZONES = [(2, 5), (13, 16)]  # Example time ranges for kill zones (UTC)
PAIRS = ["GOLD", "USOIL", "EURUSD", "GBPUSD", "BTCUSD", "USDJPY"]

DERIV_API_KEY = "GvGXa7fkjTDlOkL"


class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ICT Trading Signal App")

        self.label = tk.Label(root, text="Trading Signals", font=("Arial", 14))
        self.label.pack(pady=10)

        self.signal_label = tk.Label(root, text="No valid trade", font=("Arial", 12))
        self.signal_label.pack(pady=20)

        self.update_signals()

    def fetch_market_data(self, pair):
        try:
            ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
            request = {"ticks": pair}
            ws.send(json.dumps(request))
            response = json.loads(ws.recv())
            ws.close()
            return response if 'tick' in response else None
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None

    def fetch_candlestick_data(self, pair, timeframe="1h", count=100):
        try:
            ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
            request = {
                "ticks_history": pair,
                "adjust_start_time": 1,
                "count": count,
                "end": "latest",
                "granularity": 3600 if timeframe == "1h" else 1800,
                "style": "candles"
            }
            ws.send(json.dumps(request))
            response = json.loads(ws.recv())
            ws.close()
            return response['candles'] if 'candles' in response else None
        except Exception as e:
            print(f"Error fetching candlestick data: {e}")
            return None

    def is_kill_zone(self):
        current_hour = datetime.datetime.utcnow().hour
        return any(start <= current_hour <= end for start, end in KILL_ZONES)

    def detect_fvg(self, market_data):
        return random.choice([True, False])

    def detect_order_blocks(self, market_data):
        return random.choice([True, False])

    def detect_mss(self, market_data):
        return random.choice([True, False])

    def detect_po3(self, market_data):
        return random.choice([True, False])

    def detect_liquidity_grab(self, market_data):
        return random.choice([True, False])

    def calculate_rsi(self, prices, period=14):
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, abs(deltas), 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        return 100 - (100 / (1 + rs))

    def apply_trading_logic(self, market_data):
        if not self.is_kill_zone():
            return None, None, None, None

        fvg = self.detect_fvg(market_data)
        order_block = self.detect_order_blocks(market_data)
        mss = self.detect_mss(market_data)
        po3 = self.detect_po3(market_data)
        liquidity_grab = self.detect_liquidity_grab(market_data)

        prices = [random.uniform(1.1900, 1.2100) for _ in range(15)]  # Placeholder
        rsi = self.calculate_rsi(prices)
        support = min(prices)
        resistance = max(prices)
        fib_retracement = support + (resistance - support) * 0.618

        if fvg and order_block and mss and po3 and liquidity_grab and (rsi < 30 or rsi > 70):
            trade = "Buy" if rsi < 30 else "Sell"
            entry = fib_retracement
            sl = entry - 0.005 if trade == "Buy" else entry + 0.005
            tp = entry + 0.010 if trade == "Buy" else entry - 0.010
            self.execute_trade(trade, entry, sl, tp)
            return trade, round(entry, 5), round(sl, 5), round(tp, 5)
        return None, None, None, None

    def execute_trade(self, trade, entry, sl, tp):
        ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
        trade_request = {
            "authorize": DERIV_API_KEY,
            "buy": 1 if trade == "Buy" else -1,
            "symbol": "",
            "price": entry,
            "stop_loss": sl,
            "take_profit": tp
        }
        ws.send(json.dumps(trade_request))
        response = json.loads(ws.recv())
        ws.close()
        return response

    def update_signals(self):
        signal_text = ""
        for pair in PAIRS:
            market_data = self.fetch_market_data(pair)
            candlestick_data = self.fetch_candlestick_data(pair)
            if not market_data or not candlestick_data:
                continue

            trade, entry, sl, tp = self.apply_trading_logic(market_data)

            if trade == "Buy":
                signal_text += f"{pair} Buy Signal - Entry: {entry}, SL: {sl}, TP: {tp}\n"
            elif trade == "Sell":
                signal_text += f"{pair} Sell Signal - Entry: {entry}, SL: {sl}, TP: {tp}\n"

        if not signal_text:
            signal_text = "No valid trade"

        self.signal_label.config(text=signal_text,
                                 fg="blue" if "Buy" in signal_text else "red" if "Sell" in signal_text else "black")
        self.root.after(300000, self.update_signals)  # Update every 5 minutes


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
