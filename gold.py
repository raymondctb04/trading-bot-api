import time

try:
    import ccxt
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from datetime import datetime
except ModuleNotFoundError as e:
    missing_module = str(e).split("No module named '")[1].split("'")[0]
    print(f"Error: The required module '{missing_module}' is not installed.")
    print("Please install the missing module using 'pip install' command and try again.")
    raise SystemExit

# Initialize exchange with a longer timeout for FXCM
exchange = ccxt.fxcm({
    'rateLimit': 1200,  # API rate limit
    'timeout': 90000,  # Set timeout to 90 seconds
    'enableRateLimit': True  # Enable automatic rate limiting
})

# Function to fetch data for any trading pair and timeframe
def fetch_data(pair='XAU/USD', timeframe='1h', limit=100):
    retries = 7
    for attempt in range(retries):
        try:
            data = exchange.fetch_ohlcv(pair, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except (ccxt.RequestTimeout, ccxt.NetworkError, ccxt.ExchangeError) as e:
            print(f"Error: {e}. Retrying {attempt + 1}/{retries}...")
            time.sleep(3 ** attempt)  # Exponential backoff
    raise Exception("Failed to fetch data after multiple retries.")

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

    premium_zone = fib_levels['50.0%'] + (swing_high - fib_levels['50.0%']) / 2
    discount_zone = fib_levels['50.0%'] - (fib_levels['50.0%'] - swing_low) / 2

    latest_price = df['close'].iloc[-1]
    signal = ""
    entry_price = latest_price
    stop_loss = take_profit = 0

    if latest_price >= premium_zone:
        signal = 'SELL'
        stop_loss = swing_high
        take_profit = fib_levels['50.0%']
        print(f"{datetime.now()} - SELL Signal | Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}")
    elif latest_price <= discount_zone:
        signal = 'BUY'
        stop_loss = swing_low
        take_profit = fib_levels['50.0%']
        print(f"{datetime.now()} - BUY Signal | Entry: {entry_price}, SL: {stop_loss}, TP: {take_profit}")
    else:
        print(f"{datetime.now()} - No clear signal. Waiting for a better entry.")

    # Save trade logs
    log_entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'latest_price': latest_price,
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
def real_time_monitoring(pair='XAU/USD', timeframes=['1h', '30m', '15m'], interval=60):
    while True:
        try:
            for timeframe in timeframes:
                print(f"Analyzing timeframe: {timeframe}")
                df = fetch_data(pair, timeframe)
                analyze_market(df)
            time.sleep(interval)  # Wait before fetching new data
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in 90 seconds...")
            time.sleep(90)  # Wait before retrying

# Start real-time monitoring
real_time_monitoring(pair='XAU/USD', timeframes=['1h', '30m', '15m'], interval=60)
