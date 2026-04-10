import pandas as pd
import numpy as np
import config
from exchange_connector import exchange
from ai_model import ai_model
from dynamic_thresholds import optimizer

def obtener_datos(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=config.TIMEFRAME, limit=200)
        df = pd.DataFrame(ohlcv, columns=["time", "open", "high", "low", "close", "volume"])
        return df
    except Exception as e:
        print(f"Error obteniendo {symbol}: {e}")
        return None

def calcular_rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def analizar(symbol):
    df = obtener_datos(symbol)
    if df is None or len(df) < 100:
        return None
    
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["rsi"] = calcular_rsi(df)
    df["returns"] = df["close"].pct_change()
    df["atr"] = calcular_atr(df)
    
    precio = float(df["close"].iloc[-1])
    rsi = float(df["rsi"].iloc[-1])
    volatilidad = df["returns"].std()
    atr_val = float(df["atr"].iloc[-1])
    
    thresholds = optimizer.optimal
    
    if volatilidad > thresholds['vol_max'] or volatilidad < thresholds['vol_min']:
        return None
    if rsi < thresholds['rsi_min'] or rsi > thresholds['rsi_max']:
        return None
    
    score = 0
    if df["ema20"].iloc[-1] > df["ema50"].iloc[-1] > df["ema200"].iloc[-1]:
        score += 1
    if precio > df["ema20"].iloc[-1]:
        score += 1
    if df["returns"].iloc[-1] > 0:
        score += 1
    if 40 < rsi < 75:
        score += 1
    
    if score < thresholds['score_min']:
        return None
    
    prob_ia = ai_model.predict_probability(df)
    if prob_ia is not None:
        prob = prob_ia
    else:
        prob_map = {2: 0.60, 3: 0.75, 4: 0.85}
        prob = prob_map.get(score, 0.55)
    
    atr_stop = atr_val * config.ATR_MULTIPLIER / precio
    atr_stop = min(atr_stop, 0.05)
    
    return {
        "symbol": symbol,
        "score": score,
        "prob": prob,
        "precio": precio,
        "volatilidad": volatilidad,
        "rsi": rsi,
        "atr": atr_val,
        "stop_loss_dinamico": -atr_stop,
        "trailing_gap": 0.5 * atr_val / precio if config.TRAILING_GAP_DINAMICO else 0.015
    }