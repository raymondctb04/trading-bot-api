import tkinter as tk
from tkinter import ttk
import websocket
import json
import numpy as np


def fetch_historical_prices(symbol, count=50):
    try:
        ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089")
        request = {
            "ticks_history": symbol,
            "count": count,
            "end": "latest",
            "style": "ticks"
        }
        ws.send(json.dumps(request))
        response = json.loads(ws.recv())
        ws.close()

        if 'history' in response and 'prices' in response['history']:
            return list(map(float, response['history']['prices']))
    except Exception as e:
        print(f"Error fetching historical prices for {symbol}: {e}")
    return []


def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None

    delta = np.diff(prices)
    gains = np.where(delta > 0, delta, 0)
    losses = np.where(delta < 0, -delta, 0)

    avg_gain = np.convolve(gains, np.ones(period) / period, mode='valid')[-1]
    avg_loss = np.convolve(losses, np.ones(period) / period, mode='valid')[-1]

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)


def calculate_fibonacci(prices):
    if len(prices) < 20:
        return {}

    high, low = max(prices), min(prices)
    levels = {
        "0.236": round(high - (0.236 * (high - low)), 2),
        "0.382": round(high - (0.382 * (high - low)), 2),
        "0.5": round(high - (0.5 * (high - low)), 2),
        "0.618": round(high - (0.618 * (high - low)), 2),
        "0.786": round(high - (0.786 * (high - low)), 2)
    }
    return levels


def is_market_structure_shift(prices, fib_levels):
    if len(prices) < 2:
        return False

    last_price = prices[-1]
    prev_price = prices[-2]

    bullish_shift = prev_price < fib_levels["0.5"] and last_price > fib_levels["0.5"]
    bearish_shift = prev_price > fib_levels["0.5"] and last_price < fib_levels["0.5"]

    return bullish_shift or bearish_shift


def analyze_market():
    symbols = {
        'V10': 'R_10', 'V25': 'R_25', 'V50': 'R_50', 'V75': 'R_75',
        'V100': 'R_100', 'Step 100': 'stpRNG'
    }
    signals = {}

    for name, symbol in symbols.items():
        prices = fetch_historical_prices(symbol, count=50)
        if len(prices) < 20:
            continue

        rsi = calculate_rsi(prices)
        fib_levels = calculate_fibonacci(prices)
        market_shift = is_market_structure_shift(prices, fib_levels)

        if market_shift and rsi is not None:
            if rsi < 30:
                signal = "Buy"
            elif rsi > 70:
                signal = "Sell"
            else:
                continue

            entry_price = prices[-1]
            risk = entry_price * 0.01
            take_profit = entry_price + (2 * risk) if signal == "Buy" else entry_price - (2 * risk)
            stop_loss = entry_price - risk if signal == "Buy" else entry_price + risk

            signals[f"{name}"] = {
                'signal': signal,
                'entry_price': round(float(entry_price), 2),
                'take_profit': round(float(take_profit), 2),
                'stop_loss': round(float(stop_loss), 2),
            }

    return signals


def update_signals():
    signals = analyze_market()
    text_output.delete(1.0, tk.END)

    for pair, details in signals.items():
        text_output.insert(tk.END, f"{pair}: {details['signal']}\n")
        text_output.insert(tk.END, f"Entry: {details['entry_price']}\n")
        text_output.insert(tk.END, f"TP: {details['take_profit']} | SL: {details['stop_loss']}\n\n")


tk_window = tk.Tk()
tk_window.title("Trading Signals")
tk_window.geometry("400x400")

text_output = tk.Text(tk_window, height=20, width=50)
text_output.pack()

update_button = ttk.Button(tk_window, text="Update Signals", command=update_signals)
update_button.pack()

tk_window.mainloop()
