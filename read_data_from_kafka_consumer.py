import json
import time
import signal
from datetime import datetime, timezone
from collections import defaultdict

from confluent_kafka import Consumer, Producer
import psycopg2
import psycopg2.extras

# ---------- CONFIG ----------
KAFKA_BOOTSTRAP = "localhost:9092"
RAW_TOPIC = "raw_trades"
CANDLES_TOPIC = "candles_1m"   # optional: where to publish finished candles
GROUP_ID = "candle_builder_group"

# Postgres connection (adjust)
PG_DSN = "dbname=binance user=amoo password=boos host=localhost port=5432"

# Candle interval in seconds
INTERVAL = 60

# ---------- DB helper ----------
pg_conn = psycopg2.connect(PG_DSN)
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

def save_candle_to_db(symbol, ts_dt, candle):
    """Insert or upsert finalized candle."""
    pg_cur.execute(
        UPSERT_SQL,
        (symbol, ts_dt, candle["open"], candle["high"], candle["low"], candle["close"], candle["volume"])
    )

# ---------- Kafka consumer + optional producer ----------
consumer = Consumer({
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest",
    "enable.auto.commit": True 
})

producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})

def produce_candle_kafka(symbol, ts_iso, candle):
    payload = {
        "symbol": symbol,
        "ts": ts_iso,
        "open": candle["open"],
        "high": candle["high"],
        "low": candle["low"],
        "close": candle["close"],
        "volume": candle["volume"]
    }
    producer.produce(CANDLES_TOPIC, key=symbol, value=json.dumps(payload))
    producer.poll(0)  # serve delivery callbacks

# ---------- In-memory state ----------
# state[symbol] = { current_bucket_ts_ms: {open,high,low,close,volume}, bucket_start_ts_ms: int }
state = {}

def bucket_start_ms(ts_ms, interval_seconds=INTERVAL):
    return ts_ms - (ts_ms % (interval_seconds * 1000))

def finalize_and_rotate(symbol, bucket_ms):
    """Persist the candle for symbol/bucket_ms, then remove it from state."""
    s = state.get(symbol)
    if not s:
        return
    if s["bucket_ms"] != bucket_ms:
        # finalize the old candle
        old_bucket = s["bucket_ms"]
        candle = s["candle"]
        ts_dt = datetime.fromtimestamp(old_bucket / 1000.0, tz=timezone.utc)
        # save to DB
        save_candle_to_db(symbol, ts_dt, candle)
        # publish to Kafka
        produce_candle_kafka(symbol, ts_dt.isoformat(), candle)
        # replace with new empty structure (will be filled by caller)
        state.pop(symbol, None)

# ---------- Kafka poll loop ----------
def handle_trade(trade):
    """
    trade is a dict like: {'s': 'BINANCE:BTCUSDT', 'p': price, 'v': volume, 't': timestamp_ms}
    """
    symbol = trade["s"]
    price = float(trade["p"])
    vol = float(trade.get("v", 0.0))
    ts_ms = int(trade["t"])

    bucket_ms = bucket_start_ms(ts_ms)

    # if there is an existing bucket for symbol and it's different -> finalize it
    if symbol in state and state[symbol]["bucket_ms"] != bucket_ms:
        finalize_and_rotate(symbol, bucket_ms)

    # create new candle if not present
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
    print("Shutting down, flushing in-memory candles...")
    # finalize all in-memory candles
    for symbol, info in list(state.items()):
        bucket_ms = info["bucket_ms"]
        candle = info["candle"]
        ts_dt = datetime.fromtimestamp(bucket_ms / 1000.0, tz=timezone.utc)
        save_candle_to_db(symbol, ts_dt, candle)
        produce_candle_kafka(symbol, ts_dt.isoformat(), candle)
    try:
        consumer.close()
    except Exception:
        pass
    producer.flush()
    pg_cur.close()
    pg_conn.close()
    print("Shutdown complete.")
    exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

consumer.subscribe([RAW_TOPIC])
print("Started candle consumer...")

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        # optionally periodically flush old buckets if needed
        continue

    if msg.error():
        print("Consumer error:", msg.error())
        continue

    # parse message value (bytes -> str -> json)
    try:
        value_str = msg.value().decode("utf-8")
        data = json.loads(value_str)
    except Exception as e:
        print("Failed to parse message:", e)
        continue

    for trade in data["data"]:
        # ensure correct fields; convert timestamp if needed
        try:
            # trade timestamps are in milliseconds
            trade_obj = {
                "s": trade["s"],
                "p": trade["p"],
                "v": trade.get("v", 0.0),
                "t": int(trade["t"])
            }
            handle_trade(trade_obj)
        except Exception as e:
            print("Bad trade:", e, trade)
            continue

    # commit offsets periodically (or use automatic commits)
    consumer.commit(asynchronous=False)
