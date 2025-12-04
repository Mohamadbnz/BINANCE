# **BINANCE – Real-Time Market Data Pipeline**

A lightweight real-time market-data system that consumes Binance candle streams, processes them, and exposes the data for visualization or downstream analytics.

Built for reliability, scalability, and clean separation of configuration and logic.

---

## 📁 **Project Structure**
```
BINANCE/
├── producer.py
├── consumer.py
├── visualizer.py
├── config.py
├── requirements.txt
└── README.md

```

---

## **Files Overview**

| File            | Description                                                        |
|-----------------|--------------------------------------------------------------------|
| `producer.py`   | Fetches live candle data from Binance and publishes it to Kafka.   |
| `consumer.py`   | Subscribes to the Kafka topic and processes candle messages.       |
| `visualizer.py` | Real-time visualization of incoming candle data.                   |
| `config.py`     | Central configuration for Kafka, topics, symbols, intervals.       |

---

## ⚙️ **Installation**

### **1. Clone the repository**
git clone git@github.com:mohammadbnz74/BINANCE.git
cd BINANCE

### **2. Install dependencies**

pip install -r requirements.txt

### **3. Configure the project**

All settings are in config.py:

KAFKA_BOOTSTRAP = "localhost:9092"

TOPIC_CANDLES = "candles_1m"

GROUP_ID = "binance_consumer_01"

BINANCE_SYMBOL = "BTCUSDT"

INTERVAL = "1m"

---

## 🚀 **Usage**
### **Start Kafka**

    docker compose up -d

### **Run the producer**

    python producer.py

Fetches live candles from Binance and publishes them to Kafka.
### **Run the consumer**

    python consumer.py

Consumes candle messages and processes them.
### **Run the visualizer**

    python visualizer.py

Displays live-updating candle charts.

---

## 📊 **Architecture Overview**

Binance API → producer.py → Kafka Topic → consumer.py → visualizer.py

    Producer handles API limits, retries, and message formatting

    Kafka provides durability, replay, and horizontal scaling

    Consumer is stateless and scalable via group.id

    Visualizer is decoupled and customizable

