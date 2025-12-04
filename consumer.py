import json
import signal
from datetime import datetime, timezone
from confluent_kafka import Consumer, Producer
import psycopg2
import logging
import config

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# -----------------------------
# Postgres Setup
# -----------------------------
pg_conn = psycopg2.connect(config.PG_DSN)
pg_conn.autocommit = True
pg_cur = pg_conn.cursor()

UPSERT_SQL = """
INSERT INTO candles_1m (symbol, ts, open, high, low, close, volume)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (symbol, ts) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume;
"""

# -----------------------------
# Kafka Setup
# -----------------------------
consumer = Consumer({
    "bootstrap.servers": config.KAFKA_BOOTSTRAP,
    "group.id": config.CONSUMER_GROUP_ID,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True
})
producer = Producer({"bootstrap.servers": config.KAFKA_BOOTSTRAP})
consumer.subscribe([config.RAW_TOPIC])

# -----------------------------
# Candle state
# -----------------------------
state = {}

def calc_bucket_ms(ts_ms, interval_seconds=config.CANDLE_INTERVAL_SECONDS):
    return ts_ms - (ts_ms % (interval_seconds * 1000))

def write_candle_to_db(symbol, ts_dt, candle):
    try:
        pg_cur.execute(UPSERT_SQL, (
            symbol, ts_dt, candle["open"], candle["high"], candle["low"],
            candle["close"], candle["volume"]
        ))
    except Exception as e:
        log.error(f"DB error saving candle {symbol} {ts_dt}: {e}")

def produce_candle(symbol, ts_iso, candle):
    payload = {
        "symbol": symbol,
        "ts": ts_iso,
        **candle
    }
    producer.produce(config.CANDLES_TOPIC, key=symbol, value=json.dumps(payload))
    producer.poll(0)

def finalize_bucket(symbol, new_bucket_ms):
    s = state.get(symbol)
    if not s or s["bucket_ms"] == new_bucket_ms:
        return
    candle = s["candle"]
    ts_dt = datetime.fromtimestamp(s["bucket_ms"] / 1000, tz=timezone.utc)
    write_candle_to_db(symbol, ts_dt, candle)
    produce_candle(symbol, ts_dt.isoformat(), candle)
    state.pop(symbol, None)

def process_trade(trade):
    symbol = trade["s"]
    price = float(trade["p"])
    vol = float(trade.get("v", 0.0))
    ts_ms = int(trade["t"])

    bucket_ms = calc_bucket_ms(ts_ms)
    if symbol in state and state[symbol]["bucket_ms"] != bucket_ms:
        finalize_bucket(symbol, bucket_ms)

    if symbol not in state:
        state[symbol] = {
            "bucket_ms": bucket_ms,
            "candle": {"open": price, "high": price, "low": price, "close": price, "volume": vol}
        }
    else:
        c = state[symbol]["candle"]
        c["high"] = max(c["high"], price)
        c["low"] = min(c["low"], price)
        c["close"] = price
        c["volume"] += vol

def shutdown(signum, frame):
    log.info("Shutting down, flushing candles...")
    for symbol, info in list(state.items()):
        ts_dt = datetime.fromtimestamp(info["bucket_ms"] / 1000, tz=timezone.utc)
        write_candle_to_db(symbol, ts_dt, info["candle"])
        produce_candle(symbol, ts_dt.isoformat(), info["candle"])
    consumer.close()
    producer.flush()
    pg_cur.close()
    pg_conn.close()
    log.info("Shutdown complete.")
    exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

log.info("Candle aggregator started...")
while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        log.error(f"Consumer error: {msg.error()}")
        continue
    try:
        data = json.loads(msg.value().decode("utf-8"))
        for trade in data["data"]:
            trade_obj = {
                "s": trade["s"],
                "p": trade["p"],
                "v": trade.get("v", 0.0),
                "t": int(trade["t"])
            }
            process_trade(trade_obj)
    except Exception as e:
        log.error(f"Error processing message: {e}")
    consumer.commit(asynchronous=False)
