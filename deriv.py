import pandas as pd
import numpy as np
import tkinter as tk
import websocket
import json

# Initialize WebSocket for Deriv
DERIV_API_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"

# RSI Calculation
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# Fibonacci Retracement Levels
def calculate_fibonacci_levels(high, low):
    diff = high - low
    return {
        "61.8%": high - 0.618 * diff,
        "50%": high - 0.5 * diff,
        "38.2%": high - 0.382 * diff
    }

# Support and Resistance Levels
def calculate_support_resistance(data):
    support = data['low'].min()
    resistance = data['high'].max()
    return support, resistance

# Generate Buy or Sell Signal Based on RSI, Fibonacci, and Support/Resistance
def generate_trade_signal(rsi_value, price, fib_levels, support, resistance):
    if rsi_value < 30 and price <= fib_levels["61.8%"] and price <= support:
        entry = price
        stop_loss = support
        take_profit = resistance
        return f"BUY SIGNAL\nEntry: {entry:.2f}\nStop Loss: {stop_loss:.2f}\nTake Profit: {take_profit:.2f}\nCurrent Price: {price:.2f}"
    elif rsi_value > 70 and price >= fib_levels["38.2%"] and price >= resistance:
        entry = price
        stop_loss = resistance
        take_profit = support
        return f"SELL SIGNAL\nEntry: {entry:.2f}\nStop Loss: {stop_loss:.2f}\nTake Profit: {take_profit:.2f}\nCurrent Price: {price:.2f}"
    return f"No Signal\nCurrent Price: {price:.2f}"

# Fetch Historical Candle Data
def fetch_candle_data(symbol, granularity=3600, count=100):
    try:
        ws = websocket.create_connection(DERIV_API_URL)
        req = json.dumps({
            "ticks_history": symbol,
            "end": "latest",
            "count": count,
            "style": "candles",
            "granularity": granularity
        })
        ws.send(req)
        response = json.loads(ws.recv())
        ws.close()
        if 'candles' in response:
            data = pd.DataFrame(response['candles'])
            data['epoch'] = pd.to_datetime(data['epoch'], unit='s')
            return data
        else:
            return None
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None

# Analyze Market for Trading Signals
def analyze_market(symbol):
    data = fetch_candle_data(symbol)
    if data is not None:
        current_price = data['close'].iloc[-1]
        rsi_value = calculate_rsi(data).iloc[-1]
        high = data['high'].max()
        low = data['low'].min()
        fib_levels = calculate_fibonacci_levels(high, low)
        support, resistance = calculate_support_resistance(data)
        signal = generate_trade_signal(rsi_value, current_price, fib_levels, support, resistance)
        return signal
    else:
        return f"Failed to fetch data for {symbol}"

# Tkinter App Setup
def run_analysis():
    symbols = {
        'R_75': 'Volatility 75 Index',
        'frxXAUUSD': 'Gold',
        'stpRNG': 'Step 100 Index',
        'stpRNG2': 'Step 200 Index'
    }
    output = ""
    for symbol, name in symbols.items():
        signal = analyze_market(symbol)
        output += f"{name} Signal:\n{signal}\n\n"
    text_area.delete('1.0', tk.END)
    text_area.insert(tk.END, output)

app = tk.Tk()
app.title("Trading Signals Display")
app.geometry('500x400')

text_area = tk.Text(app, wrap=tk.WORD, width=60, height=15, font=('Arial', 12))
text_area.pack(padx=10, pady=10)

refresh_button = tk.Button(app, text="Check Signals", command=run_analysis, bg='#4CAF50', fg='white', font=('Arial', 12, 'bold'))
refresh_button.pack(pady=5)

# Auto-update every 1 minute for real-time updates
def auto_update():
    run_analysis()
    app.after(60000, auto_update)  # 60,000 ms = 1 minute

auto_update()
app.mainloop()
