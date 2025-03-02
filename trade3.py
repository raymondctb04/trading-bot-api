import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import websocket  # For live data
import json
import threading

# Constants
SYMBOL = "stpRNG"  # Step 100 Index on Deriv
WS_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"


# Main Trading App Class
class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Step 100 Index Trading Signals")
        self.root.geometry("800x600")
        self.root.configure(bg='#1e1e1e')

        # Price data for indicators
        self.prices = []

        # UI Components
        self.signal_label = tk.Label(root, text="Signal: Analyzing...", font=("Helvetica", 14), fg="white",
                                     bg='#1e1e1e')
        self.signal_label.pack(pady=10)

        # Chart setup
        self.figure, self.ax = plt.subplots(figsize=(6, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(pady=20)

        # Start WebSocket connection in a separate thread
        threading.Thread(target=self.start_websocket, daemon=True).start()

    def start_websocket(self):
        def on_message(ws, message):
            data = json.loads(message)
            if 'tick' in data:
                price = float(data['tick']['quote'])
                self.prices.append(price)
                if len(self.prices) > 100:
                    self.prices.pop(0)
                self.perform_analysis()

        def on_error(ws, error):
            messagebox.showerror("WebSocket Error", f"{error}")

        def on_close(ws, close_status_code, close_msg):
            print("WebSocket closed")

        def on_open(ws):
            subscribe_message = json.dumps({
                "ticks": SYMBOL
            })
            ws.send(subscribe_message)

        ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error, on_close=on_close,
                                    on_open=on_open)
        ws.run_forever()

    def perform_analysis(self):
        if len(self.prices) < 10:
            return  # Not enough data for analysis

        # Calculate simple moving average
        sma = np.mean(self.prices[-10:])
        entry_price = round(self.prices[-1], 2)
        take_profit = round(entry_price + 1.5, 2)  # Example TP
        stop_loss = round(entry_price - 1.5, 2)  # Example SL

        # Display trading signal
        if entry_price > sma:
            signal = f"Buy at ${entry_price}, TP: ${take_profit}, SL: ${stop_loss}"
        else:
            signal = f"Sell at ${entry_price}, TP: ${stop_loss}, SL: ${take_profit}"
        self.signal_label.config(text=signal)
        self.update_chart(entry_price, take_profit, stop_loss)

    def update_chart(self, entry_price, take_profit, stop_loss):
        self.ax.clear()
        self.ax.plot(self.prices, color='cyan', label='Step 100 Index Price')
        self.ax.axhline(entry_price, color='green', linestyle='--', label=f'Entry: ${entry_price}')
        self.ax.axhline(take_profit, color='blue', linestyle='--', label=f'TP: ${take_profit}')
        self.ax.axhline(stop_loss, color='red', linestyle='--', label=f'SL: ${stop_loss}')

        self.ax.set_title('Price Analysis', color='white')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='white')
        self.ax.legend(facecolor='#1e1e1e', edgecolor='white')
        self.figure.patch.set_facecolor('#1e1e1e')
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
