# ======================================
# CONFIGURACIÓN PRINCIPAL - BOT ADAPTATIVO CON IA
# ======================================

# ---------- MODO ----------
SIMULATION_MODE = True          # True = simulación sin órdenes reales, False = trading real
EXCHANGE_NAME = "okx"           # "okx" o "binance"

# ---------- CAPITAL Y RIESGO ----------
CAPITAL_INICIAL = 1000
MAX_POSICIONES = 3
USO_CAPITAL = 0.60

# ---------- PARÁMETROS DINÁMICOS ----------
RSI_MIN_BASE = 45
RSI_MAX_BASE = 70
VOLATILIDAD_MAX_BASE = 0.10
VOLATILIDAD_MIN_BASE = 0.003
SCORE_MINIMO_BASE = 3
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5
TRAILING_GAP_DINAMICO = True

# ---------- IA Y APRENDIZAJE ----------
RETRAIN_EVERY_TRADES = 50
OPTIMIZE_EVERY_HOURS = 4
LOOKBACK_DAYS = 30

# ---------- KELLY FRACCIONAL ----------
KELLY_FRACTION = 0.2

# ---------- COOLDOWN DINÁMICO ----------
COOLDOWN_BASE = 20
COOLDOWN_MAX = 90
COOLDOWN_MIN = 5

# ---------- TIMEFRAMES ----------
TIMEFRAME = "5m"
CYCLE_TIME = 15

# ---------- UNIVERSO DE ACTIVOS ----------
CRYPTOS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "ADA/USDT",
    "LINK/USDT", "ATOM/USDT", "INJ/USDT", "NEAR/USDT", "APT/USDT",
    "OP/USDT", "RENDER/USDT", "AR/USDT", "POL/USDT", "XRP/USDT"
]

# ---------- CORRELACIÓN ----------
CORRELACION = {
    "L1": ["BTC/USDT", "ETH/USDT"],
    "L2": ["SOL/USDT", "AVAX/USDT"],
    "L3": ["ADA/USDT", "XRP/USDT", "POL/USDT"],
    "L4": ["LINK/USDT", "ATOM/USDT"],
    "L5": ["INJ/USDT", "NEAR/USDT", "APT/USDT"],
    "L6": ["OP/USDT", "AR/USDT", "RENDER/USDT"]
}

# ---------- API KEYS (cambia después por las tuyas) ----------
OKX_API_KEY = "TU_API_KEY"
OKX_SECRET_KEY = "TU_SECRET"
OKX_PASSPHRASE = "TU_PASSPHRASE"

BINANCE_API_KEY = "TU_API_KEY"
BINANCE_SECRET_KEY = "TU_SECRET"
