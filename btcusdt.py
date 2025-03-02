import ccxt
import pandas as pd
import numpy as np
import time
import tkinter as tk
from tkinter import scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Initialize Binance Exchange
exchange = ccxt.binance()


# RSI Calculation
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# Fetch Historical Data
def fetch_data(pair='BTC/USDT', timeframe='1h', limit=100):
    ohlcv = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df


# Analyze Data
def analyze_market(pair='BTC/USDT'):
    results = ""
    timeframes = ['1h', '30m', '15m']
    analysis_data = {}
    for timeframe in timeframes:
        results += f'Analyzing {pair} on {timeframe} timeframe\n'
        df = fetch_data(pair, timeframe)

        # Support and Resistance
        df['support'] = df['low'].rolling(window=20).min()
        df['resistance'] = df['high'].rolling(window=20).max()

        # RSI Calculation
        df['rsi'] = calculate_rsi(df)

        # Fibonacci Levels
        recent_high = df['high'].max()
        recent_low = df['low'].min()
        fib_levels = {
            '0.236': recent_high - 0.236 * (recent_high - recent_low),
            '0.382': recent_high - 0.382 * (recent_high - recent_low),
            '0.5': recent_high - 0.5 * (recent_high - recent_low),
            '0.618': recent_high - 0.618 * (recent_high - recent_low),
        }

        # Generate Signals
        current_price = df['close'].iloc[-1]
        support = df['support'].iloc[-1]
        resistance = df['resistance'].iloc[-1]
        rsi = df['rsi'].iloc[-1]

        if current_price <= fib_levels['0.618'] and current_price <= support and rsi < 30:
            results += f'BUY Signal on {pair} ({timeframe}): Entry at {current_price}, SL at {recent_low}, TP at {fib_levels["0.5"]}\n'
        elif current_price >= fib_levels['0.236'] and current_price >= resistance and rsi > 70:
            results += f'SELL Signal on {pair} ({timeframe}): Entry at {current_price}, SL at {recent_high}, TP at {fib_levels["0.5"]}\n'
        else:
            results += f'No clear signal on {pair} ({timeframe}). Current price: {current_price}, RSI: {rsi}\n'

        analysis_data[timeframe] = df
    return results, analysis_data


# Tkinter App Setup

def run_analysis():
    output, analysis_data = analyze_market('BTC/USDT')
    text_area.delete('1.0', tk.END)
    text_area.insert(tk.END, output)
    plot_data(analysis_data)


# Plotting Function
def plot_data(data):
    fig, axes = plt.subplots(3, 1, figsize=(8, 12))
    timeframes = ['1h', '30m', '15m']
    for i, timeframe in enumerate(timeframes):
        df = data[timeframe]
        axes[i].plot(df['timestamp'], df['close'], label='Close Price', color='blue')
        axes[i].plot(df['timestamp'], df['support'], label='Support', linestyle='--', color='green')
        axes[i].plot(df['timestamp'], df['resistance'], label='Resistance', linestyle='--', color='red')
        axes[i].set_title(f'{timeframe} Timeframe Analysis')
        axes[i].legend()
    plt.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=10)


app = tk.Tk()
app.title("BTC/USDT Trading Signal Analyzer with Visuals")
app.geometry('800x800')

text_area = scrolledtext.ScrolledText(app, wrap=tk.WORD, width=70, height=10)
text_area.pack(padx=10, pady=10)

refresh_button = tk.Button(app, text="Run Analysis", command=run_analysis, bg='#4CAF50', fg='white',
                           font=('Arial', 12, 'bold'))
refresh_button.pack(pady=5)


# Auto-update every 15 minutes
def auto_update():
    run_analysis()
    app.after(900000, auto_update)  # 900,000 ms = 15 minutes


auto_update()
app.mainloop()
