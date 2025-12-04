# 🚀 Real-Time Cryptocurrency Market Data Pipeline

A **pipeline** that ingests live cryptocurrency market data from Binance WebSocket, processes it through Apache Kafka, and enables real-time analytics and visualization.

**Built to demonstrate:** Stream processing • Event-driven architecture • Scalable data engineering • Real-time analytics

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Kafka](https://img.shields.io/badge/Kafka-3.0+-orange)
![License](https://img.shields.io/badge/license-MIT-green)

[Live Demo Video](link-if-you-have-one) | [Architecture Diagram](https://github.com/Mohamadbnz/BINANCE/edit/main/README.md#%EF%B8%8F-architecturehttps://github.com/Mohamadbnz/BINANCE/edit/main/README.md#%EF%B8%8F-architecture)

---

## 🎯 Key Features

- ⚡ **Real-time streaming** with sub-second latency
- 🔄 **Event-driven architecture** using Apache Kafka
- 📊 **Live visualization** with candlestick charts
- 📈 **Scalable design** supporting multiple symbols/intervals
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

## 🏗️ Architecture
```
┌─────────────────────┐
│   Binance WebSocket │  (Live market data)
│   API (BTCUSDT 1m)  │
└──────────┬──────────┘
           │ candle updates
           ▼
    ┌──────────────┐
    │  Producer    │  (producer.py)
    │  • Connects  │
    │  • Validates │
    │  • Publishes │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │   Apache Kafka       │
    │   Topic: candles_1m  │  (Message queue)
    │   • Persistence      │
    │   • Replay capability│
    └──────┬───────────────┘
           │
           ├─────────────────┐
           ▼                 ▼
    ┌──────────┐    ┌──────────────┐
    │Consumer  │    │ Visualizer   │
    │(Group 1) │    │ • Real-time  │
    │Storage │      │ • Candlestick│
    └──────────┘    └──────────────┘
```

**Design Principles:**
- **Decoupling**: Components communicate via Kafka, can be deployed independently
- **Scalability**: Add more consumers without affecting producer
- **Fault Tolerance**: Kafka persists messages if consumer fails
- **Replayability**: Can reprocess historical data from any point

    Visualizer is decoupled and customizable

