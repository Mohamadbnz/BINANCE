from confluent_kafka import Consumer
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, date2num
from datetime import datetime
import matplotlib.ticker as mticker
import time

# ---------------- CONFIG ----------------
KAFKA_BOOTSTRAP = "localhost:9092"
CANDLES_TOPIC = "candles_1m"
GROUP_ID = "candle_visualization_group"

consumer = Consumer({
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest",
    # "enable.auto.commit": True
})
consumer.subscribe([CANDLES_TOPIC])

# Keep last N candles
candles_df = pd.DataFrame(columns=["ts","open","high","low","close","volume"])

# Setup Matplotlib interactive mode
plt.ion()
fig, ax = plt.subplots(figsize=(10,5))

def plot_candles(df):
    ax.clear()
    df_plot = df.copy()
    df_plot["ts_num"] = df_plot["ts"].apply(date2num)
    for i, row in df_plot.iterrows():
        color = "green" if row["close"] >= row["open"] else "red"
        ax.plot([row["ts_num"], row["ts_num"]], [row["low"], row["high"]], color=color)
        ax.plot([row["ts_num"], row["ts_num"]], [row["open"], row["close"]], color=color, linewidth=5)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    plt.title("Live Candles")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.draw()
    plt.pause(0.1)

print("Starting live candle plot...")

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        time.sleep(0.1)
        continue

    if msg.error():
        print("Consumer error:", msg.error())
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
        candles_df = candles_df.tail(50)  # last 50 candles
        plot_candles(candles_df)
    except Exception as e:
        print("Error:", e)
