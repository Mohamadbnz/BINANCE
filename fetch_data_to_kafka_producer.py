import websocket
import json
from confluent_kafka import Producer

API_KEY = "d4gv219r01qgvvc5ahv0d4gv219r01qgvvc5ahvg"
SYMBOLS = ["BINANCE:BTCUSDT"]

kafka_producer = Producer({'bootstrap.servers': 'localhost:9092'})

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_message(ws, message):
    try:
        msg = json.loads(message)
        if msg.get("type") != "trade":
            return
        
        payload = json.dumps(msg)
        kafka_producer.produce(
            topic="raw_trades",
            key=msg["data"][0]["s"],
            value=payload
        )
        kafka_producer.poll(0)  # Add this for delivery reports
        
    except Exception as e:
        print(f"Error in on_message: {e}")

def on_open(ws):
    for sym in SYMBOLS:
        ws.send(json.dumps({"type": "subscribe", "symbol": sym}))

def on_close(ws, close_status_code, close_msg):
    print("### closed ###", close_status_code, close_msg)

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={API_KEY}",
        on_message=on_message,
        on_error=on_error,  # Add this
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()
