import json
import time
import logging
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, DateFormatter
from confluent_kafka import Consumer
import config
from threading import Thread

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# -----------------------------
# Kafka Consumer
# -----------------------------
consumer = Consumer({
    "bootstrap.servers": config.KAFKA_BOOTSTRAP,
    "group.id": config.VISUALIZER_GROUP_ID,
    "auto.offset.reset": "earliest"
})
consumer.subscribe([config.CANDLES_TOPIC])

candles_df = pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])

# -----------------------------
# Matplotlib setup
# -----------------------------
plt.ion()
fig, ax = plt.subplots(figsize=(12, 6))

def plot_candles(df):
    ax.clear()
    df_plot = df.copy()
    df_plot["ts_num"] = df_plot["ts"].apply(date2num)
    for _, row in df_plot.iterrows():
        color = "green" if row["close"] >= row["open"] else "red"
        # High-low line
        ax.plot([row["ts_num"], row["ts_num"]], [row["low"], row["high"]], color=color)
        # Open-close line (thicker)
        ax.plot([row["ts_num"], row["ts_num"]], [row["open"], row["close"]], color=color, linewidth=5)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    plt.title("Live Candles")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.draw()
    plt.pause(0.001)  # small pause to update

# -----------------------------
# Kafka polling in a separate thread
# -----------------------------
def kafka_listener():
    global candles_df
    while True:
        msg = consumer.poll(0.5)
        if msg is None:
            continue
        if msg.error():
            log.error(f"Consumer error: {msg.error()}")
            continue
        try:
            data = json.loads(msg.value().decode("utf-8"))
            ts = pd.to_datetime(data["ts"])
            new_row = {
                "ts": ts,
                "open": data["open"],
                "high": data["high"],
                "low": data["low"],
                "close": data["close"],
                "volume": data["volume"]
            }
            candles_df = pd.concat([candles_df, pd.DataFrame([new_row])], ignore_index=True)
            candles_df = candles_df.tail(config.MAX_CANDLES_TO_KEEP)
        except Exception as e:
            log.error(f"Error processing candle: {e}")

Thread(target=kafka_listener, daemon=True).start()

# -----------------------------
# Main plotting loop (updates every 0.5s)
# -----------------------------
log.info("Starting candle visualizer...")
while True:
    if not candles_df.empty:
        plot_candles(candles_df)
    time.sleep(0.5)
