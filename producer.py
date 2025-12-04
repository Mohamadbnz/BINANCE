import websocket
import json
from confluent_kafka import Producer
import logging
import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

producer = Producer({"bootstrap.servers": config.KAFKA_BOOTSTRAP})

def on_message(ws, message):
    try:
        msg = json.loads(message)
        if msg.get("type") != "trade":
            return
        producer.produce(
            topic=config.RAW_TOPIC,
            key=msg["data"][0]["s"],
            value=json.dumps(msg)
        )
        producer.poll(0)

    except Exception as e:
        log.error(f"Error processing message: {e}")

def on_open(ws):
    for symbol in config.SYMBOLS:
        ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))
    log.info(f"Subscribed to symbols: {config.SYMBOLS}")

def on_error(ws, error):
    log.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    log.info(f"WebSocket closed: {close_status_code}, {close_msg}")

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={config.FINNHUB_API_KEY}",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()
