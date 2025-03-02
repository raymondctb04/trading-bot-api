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

# Liquidity Grabs Detection

def detect_liquidity_grabs(data):
    high_liquidity = data['high'].nlargest(3).min()
    low_liquidity = data['low'].nsmallest(3).max()
    return high_liquidity, low_liquidity

# Analyze market with combined ICT strategy

def analyze_market():
    symbol = 'cryBTCUSD'
    timeframes = {'1h': '3600', '30m': '1800', '15m': '900'}
    signals = {}

    for tf_label, tf in timeframes.items():
        data = fetch_data(symbol, tf)
        if data is not None:
            data['rsi'] = calculate_rsi(data)
            fib_levels = fibonacci_levels(data)
            support, resistance = support_resistance_levels(data)
            high_liquidity, low_liquidity = detect_liquidity_grabs(data)
            current_price = data['close'].iloc[-1]
            rsi_value = data['rsi'].iloc[-1]

            if rsi_value < 30 and current_price <= fib_levels['0.618'] and current_price > support and current_price > low_liquidity:
                signal = 'Buy'
                entry_price = current_price
                take_profit = fib_levels['0.382']
                stop_loss = entry_price - (take_profit - entry_price) * 0.5  # 1:2 RR
            elif rsi_value > 70 and current_price >= fib_levels['0.618'] and current_price < resistance and current_price < high_liquidity:
                signal = 'Sell'
                entry_price = current_price
                take_profit = fib_levels['0.786']
                stop_loss = entry_price + (entry_price - take_profit) * 0.5  # 1:2 RR
            else:
                continue  # Skip if there's no clear Buy or Sell signal

            signals[tf_label] = {
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
    for tf, details in signals.items():
        if isinstance(details, dict):
            output += (
                f"Timeframe: {tf}\n"
                f"Signal: {details['signal']}\n"
                f"Entry Price: {details['entry_price']:.2f}\n"
                f"Take Profit: {details['take_profit']:.2f}\n"
                f"Stop Loss: {details['stop_loss']:.2f}\n"
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
app.title("Advanced ICT Trading Signals")
app.geometry("600x400")

label = tk.Label(app, text="TRADINGBOT1", font=("Helvetica", 16))
label.pack(pady=20)

signal_text = tk.StringVar()
signal_display = tk.Label(app, textvariable=signal_text, font=("Helvetica", 10), justify=tk.LEFT, anchor='w')
signal_display.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Run scheduled updates in a separate thread
threading.Thread(target=scheduled_updates, daemon=True).start()

app.mainloop()
