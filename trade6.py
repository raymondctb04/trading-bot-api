import tkinter as tk
from tkinter import messagebox
import pandas as pd
import numpy as np
import time
import threading
import websocket
import json

# Function to fetch historical data using WebSocket
def fetch_data(symbol, timeframe, count=200):
    data = []
    try:
        ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
        request = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "granularity": int(timeframe),
            "style": "candles"
        }
        ws.send(json.dumps(request))
        response = json.loads(ws.recv())
        ws.close()
        if 'candles' in response:
            candles = response['candles']
            df = pd.DataFrame(candles)
            if all(col in df.columns for col in ['open', 'close', 'high', 'low']):
                return df
    except Exception as e:
        print(f"Error fetching data for {symbol} on timeframe {timeframe}: {e}")
    return None

# Function to fetch the latest price
def fetch_latest_price(symbol):
    try:
        ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
        request = {"ticks": symbol}
        ws.send(json.dumps(request))
        response = json.loads(ws.recv())
        ws.close()
        if 'tick' in response:
            return response['tick']['quote']
    except Exception as e:
        print(f"Error fetching latest price for {symbol}: {e}")
    return None

# RSI Calculation
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Analyze market with combined ICT strategy
def analyze_market():
    symbols = {
        'Gold': 'frxXAUUSD',
        'USOIL': 'frxUSOIL',
        'EURUSD': 'frxEURUSD',
        'USDJPY': 'frxUSDJPY',
        'GBPUSD': 'frxGBPUSD'
    }
    timeframes = {'1h': '3600', '30m': '1800', '15m': '900'}
    signals = {}

    for name, symbol in symbols.items():
        latest_price = fetch_latest_price(symbol)
        for tf_label, tf in timeframes.items():
            data = fetch_data(symbol, tf)
            if data is not None and latest_price:
                data['rsi'] = calculate_rsi(data)
                current_price = float(latest_price)
                rsi_value = data['rsi'].iloc[-1]

                if rsi_value < 30:
                    signal = 'Buy'
                    entry_price = current_price
                    stop_loss = entry_price - 0.0050  # 50 pips
                    take_profit = entry_price + 0.0100  # 100 pips
                elif rsi_value > 70:
                    signal = 'Sell'
                    entry_price = current_price
                    stop_loss = entry_price + 0.0050  # 50 pips
                    take_profit = entry_price - 0.0100  # 100 pips
                else:
                    continue  # Skip if there's no clear Buy or Sell signal

                decimal_places = 5 if symbol in ['frxEURUSD', 'frxGBPUSD', 'frxUSDJPY'] else 2
                signals[f"{name} - {tf_label}"] = {
                    'signal': signal,
                    'entry_price': round(float(entry_price), decimal_places),
                    'take_profit': round(float(take_profit), decimal_places),
                    'stop_loss': round(float(stop_loss), decimal_places),
                }
    return signals if signals else {'No Clear Trading Signal': 'No valid Buy or Sell signals found.'}

# GUI using Tkinter
def update_signals():
    signals = analyze_market()
    output = ""
    last_update = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    for pair, details in signals.items():
        if isinstance(details, dict):
            output += (
                f"Pair: {pair}\n"
                f"Signal: {details['signal']}\n"
                f"Entry Price: {details['entry_price']}\n"
                f"Take Profit: {details['take_profit']}\n"
                f"Stop Loss: {details['stop_loss']}\n"
                f"Last Update: {last_update}\n\n"
            )
        else:
            output += f"{details}\n\n"
    signal_text.set(output)

# Schedule data updates
def scheduled_updates():
    while True:
        update_signals()
        time.sleep(300)  # Update every 5 minutes

# Main Tkinter window
app = tk.Tk()
app.title("Multi-Pair Trading Signals")
app.geometry("700x500")

label = tk.Label(app, text="REAL-TIME TRADING SIGNALS", font=("Helvetica", 16))
label.pack(pady=20)

signal_text = tk.StringVar()
signal_display = tk.Label(app, textvariable=signal_text, font=("Helvetica", 10), justify=tk.LEFT, anchor='w')
signal_display.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Run scheduled updates in a separate thread
threading.Thread(target=scheduled_updates, daemon=True).start()

app.mainloop()
