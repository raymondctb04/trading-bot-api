import tkinter as tk
from tkinter import messagebox
import numpy as np
import websocket  # For live data
import json
import threading
import time

# Constants
SYMBOLS = ["1HZ100V"]  # VOLATILITY 100(1S) INDEX
WS_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"


# Main Trading App Class
class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Volatility 100(1S) Index Trading Signals")
        self.root.geometry("800x400")
        self.root.configure(bg='#1e1e1e')

        # Price data for indicators
        self.prices = {symbol: [] for symbol in SYMBOLS}
        self.last_signal_time = {symbol: 0 for symbol in SYMBOLS}  # Track last signal time

        # UI Components
        self.signal_label = tk.Label(root, text="Signal: Analyzing...", font=("Helvetica", 14), fg="white",
                                     bg='#1e1e1e')
        self.signal_label.pack(pady=10)

        # Start WebSocket connection in a separate thread
        for symbol in SYMBOLS:
            threading.Thread(target=self.start_websocket, args=(symbol,), daemon=True).start()

    def start_websocket(self, symbol):
        def on_message(ws, message):
            data = json.loads(message)
            if 'tick' in data:
                price = float(data['tick']['quote'])
                self.prices[symbol].append(price)
                if len(self.prices[symbol]) > 100:
                    self.prices[symbol].pop(0)
                self.perform_ict_analysis(symbol)

        def on_error(ws, error):
            messagebox.showerror("WebSocket Error", f"{error}")

        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed for {symbol}")

        def on_open(ws):
            subscribe_message = json.dumps({
                "ticks": symbol,
                "subscribe": 1
            })
            ws.send(subscribe_message)

        ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error, on_close=on_close,
                                    on_open=on_open)
        ws.run_forever()

    def detect_fvg(self, prices):
        if len(prices) < 3:
            return False
        return abs(prices[-3] - prices[-1]) > 2 * abs(prices[-2] - prices[-1])

    def detect_order_block(self, prices):
        if len(prices) < 5:
            return False
        recent_range = prices[-5:]
        high = max(recent_range)
        low = min(recent_range)
        return prices[-1] <= low or prices[-1] >= high

    def detect_liquidity_grab(self, prices):
        if len(prices) < 10:
            return False
        highs = [max(prices[i:i + 3]) for i in range(-10, -3)]
        return prices[-1] > max(highs)

    def perform_ict_analysis(self, symbol):
        prices = self.prices[symbol]
        current_time = time.time()

        # Only update signal every 60 seconds
        if current_time - self.last_signal_time[symbol] < 60:
            return

        self.last_signal_time[symbol] = current_time

        if len(prices) < 10:
            return  # Not enough data for analysis

        entry_price = round(prices[-1], 2)
        take_profit = round(entry_price + 2.0, 2)  # Example TP
        stop_loss = round(entry_price - 2.0, 2)  # Example SL

        # ICT Strategy-Based Signals
        if self.detect_fvg(prices):
            signal = f"{symbol}: BUY (Fair Value Gap) - Entry: {entry_price}, TP: {take_profit}, SL: {stop_loss}"
        elif self.detect_order_block(prices):
            signal = f"{symbol}: SELL (Order Block) - Entry: {entry_price}, TP: {stop_loss}, SL: {take_profit}"
        elif self.detect_liquidity_grab(prices):
            signal = f"{symbol}: BUY (Liquidity Grab) - Entry: {entry_price}, TP: {take_profit}, SL: {stop_loss}"
        else:
            signal = f"{symbol}: No clear entry"

        self.signal_label.config(text=signal)


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
