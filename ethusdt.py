import time
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Binance API base URL
base_url = 'https://api.binance.com'

# Function to fetch data for any trading pair and timeframe

def fetch_data(pair='ETHUSDT', timeframe='1h', limit=100):
    endpoint = f"{base_url}/api/v3/klines"
    params = {
        'symbol': pair,
        'interval': timeframe,
        'limit': limit
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    df = pd.DataFrame([{
        'timestamp': int(candle[0]),
        'open': float(candle[1]),
        'high': float(candle[2]),
        'low': float(candle[3]),
        'close': float(candle[4]),
        'volume': float(candle[5])
    } for candle in data])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# Function to identify support and resistance levels

def identify_support_resistance(df):
    supports = df['low'].rolling(window=20).min()
    resistances = df['high'].rolling(window=20).max()
    return supports, resistances

# Function to calculate RSI
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to analyze data and provide signals with entry, stop loss, and take profit

def analyze_market(df):
    swing_high = df['high'].max()
    swing_low = df['low'].min()

    # Fibonacci levels
    fib_levels = {
        '0.0%': swing_high,
        '23.6%': swing_high - 0.236 * (swing_high - swing_low),
        '38.2%': swing_high - 0.382 * (swing_high - swing_low),
        '50.0%': swing_high - 0.5 * (swing_high - swing_low),
        '61.8%': swing_high - 0.618 * (swing_high - swing_low),
        '100%': swing_low
    }

    supports, resistances = identify_support_resistance(df)
    rsi = calculate_rsi(df)

    premium_zone = fib_levels['50.0%'] + (swing_high - fib_levels['50.0%']) / 2
    discount_zone = fib_levels['50.0%'] - (fib_levels['50.0%'] - swing_low) / 2

    latest_price = df['close'].iloc[-1]
    latest_support = supports.iloc[-1]
    latest_resistance = resistances.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    signal = ""
    entry_price = latest_price
    stop_loss = take_profit = 0

    if latest_price >= premium_zone and latest_price >= latest_resistance and latest_rsi > 70:
        signal = 'SELL'
        stop_loss = swing_high
        take_profit = fib_levels['50.0%']
        print(f"{datetime.now()} - SELL Signal | Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}, RSI: {latest_rsi}")
    elif latest_price <= discount_zone and latest_price <= latest_support and latest_rsi < 30:
        signal = 'BUY'
        stop_loss = swing_low
        take_profit = fib_levels['50.0%']
        print(f"{datetime.now()} - BUY Signal | Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}, RSI: {latest_rsi}")
    else:
        print(f"{datetime.now()} - No clear signal. Waiting for a better entry. RSI: {latest_rsi}")

    # Save trade logs
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'latest_price': latest_price,
        'support': latest_support,
        'resistance': latest_resistance,
        'rsi': latest_rsi,
        'signal': signal,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit
    }
    try:
        log_df = pd.read_csv('trade_logs.csv')
        log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
    except FileNotFoundError:
        log_df = pd.DataFrame([log_entry])
    log_df.to_csv('trade_logs.csv', index=False)

# Continuous monitoring loop for multiple timeframes

def real_time_monitoring(pair='ETHUSDT', timeframes=['1h', '30m', '15m'], interval=900):
    while True:
        try:
            for timeframe in timeframes:
                print(f"Analyzing timeframe: {timeframe}")
                df = fetch_data(pair, timeframe)
                analyze_market(df)
            time.sleep(interval)  # Wait before fetching new data every 15 minutes
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in 90 seconds...")
            time.sleep(90)  # Wait before retrying

# Start real-time monitoring
real_time_monitoring(pair='ETHUSDT', timeframes=['1h', '30m', '15m'], interval=900)
6