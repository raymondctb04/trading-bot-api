from flask import Flask, jsonify
import json
import websocket
import threading
import datetime

app = Flask(__name__)

DERIV_API_URL = "wss://ws.derivws.com/websockets/v3?app_id=1089"
SYMBOLS = ["frxXAUUSD", "frxEURUSD", "frxGBPUSD", "frxUSDJPY", "cryBTCUSD", "R_75", "R_50", "R_10", "R_100"]

live_data = {}

def on_message(ws, message):
    """Handles incoming WebSocket messages"""
    data = json.loads(message)
    if "tick" in data:
        symbol = data["tick"]["symbol"]
        price = float(data["tick"]["quote"])
        session = get_trading_session()
        signal = "Hold"  # Implement actual signal logic

        live_data[symbol] = {"price": price, "session": session, "signal": signal}

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_open(ws):
    """Subscribes to live price updates for symbols"""
    for symbol in SYMBOLS:
        ws.send(json.dumps({"ticks": symbol}))

def get_trading_session():
    """Determines the current trading session"""
    current_hour = datetime.datetime.utcnow().hour
    if 0 <= current_hour < 8:
        return "Asian"
    elif 8 <= current_hour < 16:
        return "London"
    else:
        return "New York"

def start_websocket():
    """Starts WebSocket connection"""
    ws = websocket.WebSocketApp(DERIV_API_URL, on_message=on_message, on_error=on_error, on_open=on_open)
    ws.run_forever()

@app.route('/get_prices', methods=['GET'])
def get_prices():
    """Returns the latest trading data"""
    return jsonify(live_data)

if __name__ == '__main__':
    ws_thread = threading.Thread(target=start_websocket)
    ws_thread.daemon = True
    ws_thread.start()
    app.run(host='0.0.0.0', port=5000)
