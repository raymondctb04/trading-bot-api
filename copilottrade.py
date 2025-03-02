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

# Fibonacci Retracement Levels
def fibonacci_levels(data):
    swing_high = data['high'].max()
    swing_low = data['low'].min()
    levels = {
        '0.236': swing_high - 0.236 * (swing_high - swing_low),
        '0.382': swing_high - 0.382 * (swing_high - swing_low),
        '0.5': swing_high - 0.5 * (swing_high - swing_low),
        '0.618': swing_high - 0.618 * (swing_high - swing_low),
        '0.786': swing_high - 0.786 * (swing_high - swing_low)
    }
    return levels

# Support and Resistance Levels
def support_resistance_levels(data):
    support = data['low'].min()
    resistance = data['high'].max()
    return support, resistance

# Analyze market with combined ICT strategy
def analyze_market():
    symbols = {
        'V10 (1s)': '1HZ10V', 'V10': 'R_10',
        'V25 (1s)': '1HZ25V', 'V25': 'R_25',
        'V50 (1s)': '1HZ50V', 'V50': 'R_50',
        'V75 (1s)': '1HZ75V', 'V75': 'R_75',
        'V100 (1s)': '1HZ100V', 'V100': 'R_100',
        'Step 100': 'stpRNG', 'Step 200': 'stpRNG2',
        'Step 300': 'stpRNG3', 'Step 400': 'stpRNG4',
        'Step 500': 'stpRNG5'
    }
    timeframes = {'1h': '3600', '30m': '1800', '15m': '900', '5m': '300'}
    signals = {}

    for name, symbol in symbols.items():
        latest_price = fetch_latest_price(symbol)
        for tf_label, tf in timeframes.items():
            data = fetch_data(symbol, tf)
            if data is not None and latest_price:
                data['rsi'] = calculate_rsi(data)
                fib_levels = fibonacci_levels(data)
                support, resistance = support_resistance_levels(data)
                current_price = float(latest_price)
                rsi_value = data['rsi'].iloc[-1]

                if rsi_value < 30 and current_price <= fib_levels['0.618'] and current_price > support:
                    signal = 'Buy'
                    entry_price = current_price
                    risk = abs(entry_price - support)
                    take_profit = entry_price + (2 * risk)
                    stop_loss = support
                elif rsi_value > 70 and current_price >= fib_levels['0.618'] and current_price < resistance:
                    signal = 'Sell'
                    entry_price = current_price
                    risk = abs(entry_price - resistance)
                    take_profit = entry_price - (2 * risk)
                    stop_loss = resistance
                else:
                    continue  # Skip if there's no clear Buy or Sell signal

                signals[f"{name} - {tf_label}"] = {
                    'signal': signal,
                    'entry_price': round(float(entry_price), 2),
                    'take_profit': round(float(take_profit), 2),
                    'stop_loss': round(float(stop_loss), 2),
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
app.title("RELAX OO ")
app.geometry("700x500")

label = tk.Label(app, text="BRAASO", font=("Helvetica", 16))
label.pack(pady=20)

signal_text = tk.StringVar()
signal_display = tk.Label(app, textvariable=signal_text, font=("Helvetica", 10), justify=tk.LEFT, anchor='w')
signal_display.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Run scheduled updates in a separate thread
threading.Thread(target=scheduled_updates, daemon=True).start()

app.mainloop()
