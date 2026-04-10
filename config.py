# ======================================
# CONFIGURACIÓN - VERSIÓN CONSERVADORA CON MÁS SEÑALES
# ======================================

# ---------- MODO ----------
SIMULATION_MODE = True
EXCHANGE_NAME = "okx"

# ---------- CAPITAL Y RIESGO ----------
CAPITAL_INICIAL = 1000
MAX_POSICIONES = 3
USO_CAPITAL = 0.60

# ---------- FILTROS EXIGENTES ----------
RSI_MIN_BASE = 45
RSI_MAX_BASE = 70
VOLATILIDAD_MAX_BASE = 0.12
VOLATILIDAD_MIN_BASE = 0.003
SCORE_MINIMO_BASE = 3          # AHORA 3 (solo señales de alta calidad)
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5
TRAILING_GAP_DINAMICO = True

# ---------- TAMAÑOS DE POSICIÓN (más conservadores) ----------
TAMANO_ELITE = 0.12            # 12% del capital actual
TAMANO_OPORTUNISTA_BUENA = 0.07 # 7% del capital actual
# ELIMINADO OPORTUNISTA_REGULAR

# ---------- COOLDOWN (más rápido para más trades) ----------
COOLDOWN_BASE = 10             # ANTES 20s
COOLDOWN_MAX = 60
COOLDOWN_MIN = 5

# ---------- TIMEFRAMES ----------
TIMEFRAME = "5m"
CYCLE_TIME = 10                # ANTES 15s

# ---------- UNIVERSO DE ACTIVOS (más grande para más oportunidades) ----------
CRYPTOS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "ADA/USDT",
    "LINK/USDT", "ATOM/USDT", "INJ/USDT", "NEAR/USDT", "APT/USDT",
    "OP/USDT", "RENDER/USDT", "AR/USDT", "POL/USDT", "XRP/USDT",
    "DOGE/USDT", "WIF/USDT", "PEPE/USDT", "SUI/USDT", "SEI/USDT"
]

# ---------- CORRELACIÓN (actualizada con nuevos activos) ----------
CORRELACION = {
    "L1": ["BTC/USDT", "ETH/USDT"],
    "L2": ["SOL/USDT", "AVAX/USDT"],
    "L3": ["ADA/USDT", "XRP/USDT", "POL/USDT"],
    "L4": ["LINK/USDT", "ATOM/USDT"],
    "L5": ["INJ/USDT", "NEAR/USDT", "APT/USDT"],
    "L6": ["OP/USDT", "AR/USDT", "RENDER/USDT"],
    "MEME": ["DOGE/USDT", "WIF/USDT", "PEPE/USDT"],
    "L1_ALT": ["SUI/USDT", "SEI/USDT"]
}

# ---------- API KEYS ----------
OKX_API_KEY = "TU_API_KEY"
OKX_SECRET_KEY = "TU_SECRET"
OKX_PASSPHRASE = "TU_PASSPHRASE"

BINANCE_API_KEY = "TU_API_KEY"
BINANCE_SECRET_KEY = "TU_SECRET"