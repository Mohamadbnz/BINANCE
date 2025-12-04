# -----------------------------
# Kafka Config
# -----------------------------
KAFKA_BOOTSTRAP = "localhost:9092"
RAW_TOPIC = "raw_trades"
CANDLES_TOPIC = "candles_1m"
PRODUCER_GROUP_ID = "producer_group"
CONSUMER_GROUP_ID = "candle_aggregator_group"
VISUALIZER_GROUP_ID = "candle_visualizer_group"

# -----------------------------
# Candle Config
# -----------------------------
CANDLE_INTERVAL_SECONDS = 60
MAX_CANDLES_TO_KEEP = 50  # for visualizer

# -----------------------------
# Postgres Config
# -----------------------------
PG_DSN = "dbname=postgres user=postgres password=postgres host=localhost port=5432"

# -----------------------------
# API Config (for WebSocket)
# -----------------------------
FINNHUB_API_KEY = "d4gv219r01qgvvc5ahv0d4gv219r01qgvvc5ahvg"
SYMBOLS = ["BINANCE:BTCUSDT"]
