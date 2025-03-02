import websocket
import json

def get_active_symbols():
    ws = websocket.create_connection("wss://ws.binaryws.com/websockets/v3?app_id=1089")
    request = {
        "active_symbols": "brief",
        "product_type": "basic"
    }
    ws.send(json.dumps(request))
    response = json.loads(ws.recv())
    ws.close()
    return response

# Fetch active symbols
symbols_response = get_active_symbols()

# Check if the response contains active symbols
if 'active_symbols' in symbols_response:
    # Print all available symbols
    for symbol_info in symbols_response['active_symbols']:
        print(f"Symbol: {symbol_info['symbol']}, Display Name: {symbol_info['display_name']}")
else:
    print("Failed to retrieve active symbols.")
