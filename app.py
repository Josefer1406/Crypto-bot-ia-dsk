from flask import Flask, jsonify
import threading
import time
import datetime
import os

import config
import portfolio

from services.scanner import analizar
from core.risk import calcular_size
from database import crear_tablas, insertar_trade, obtener_trades

app = Flask(__name__)

# =========================
# API
# =========================
@app.route("/")
def home():
    return "🚀 QUANT ENGINE - ENTRENAMIENTO ESTABLE"

@app.route("/data")
def data():
    rows = obtener_trades()

    return jsonify([
        {
            "fecha": r[1],
            "symbol": r[2],
            "tipo": r[3],
            "precio": float(r[4]),
            "size": float(r[5]),
            "pnl": float(r[6]),
            "capital": float(r[7])
        } for r in rows
    ])

# =========================
# BOT ENGINE
# =========================
def run_bot():

    print("🚀 ENGINE INSTITUCIONAL (FASE ENTRENAMIENTO)")

    portfolio.cargar_estado()
    crear_tablas()

    while True:
        try:

            print("\n🔎 Analizando mercado...")

            ranking = []

            # =========================
            # SCANNER
            # =========================
            for symbol in config.CRYPTOS:
                try:
                    score, precio, decision, prob = analizar(symbol)

                    # 🔥 convertir numpy → python
                    precio = float(precio)
                    prob = float(prob)

                    print(f"{symbol} | score: {score} | prob: {round(prob,2)}")

                    ranking.append((symbol, score, precio, decision, prob))

                except Exception as e:
                    print(f"❌ Error {symbol}: {e}")

            if not ranking:
                print("⚠️ Sin datos")
                time.sleep(config.CYCLE_TIME)
                continue

            # =========================
            # ORDENAMIENTO
            # =========================
            ranking.sort(key=lambda x: (x[1], x[4]), reverse=True)

            top = ranking[:config.MAX_POSICIONES]

            print("\n🏆 TOP OPORTUNIDADES:")
            for t in top:
                print(t)

            # =========================
            # CIERRES
            # =========================
            for symbol in list(portfolio.posiciones.keys()):

                precio_actual = next(
                    (p for s, sc, p, d, pr in ranking if s == symbol),
                    None
                )

                if precio_actual and portfolio.evaluar_salida(symbol, precio_actual):

                    size = portfolio.posiciones[symbol]["size"]
                    pnl = portfolio.cerrar_posicion(symbol, precio_actual)

                    insertar_trade(
                        datetime.datetime.now(),
                        symbol,
                        "SELL",
                        float(precio_actual),
                        float(size),
                        float(pnl),
                        float(portfolio.capital)
                    )

                    print(f"🔴 SELL {symbol} | PnL: {round(pnl,2)}")

            # =========================
            # APERTURAS (🔥 CLAVE)
            # =========================
            for symbol, score, precio, decision, prob in top:

                # 🔥 ignoramos decision ML en entrenamiento
                if score >= 1:

                    size = calcular_size(precio, score, prob)

                    if portfolio.abrir_posicion(symbol, precio, size):

                        insertar_trade(
                            datetime.datetime.now(),
                            symbol,
                            "BUY",
                            float(precio),
                            float(size),
                            0.0,
                            float(portfolio.capital)
                        )

                        print(f"🟢 BUY {symbol} | score: {score}")

            print(f"\n💰 Capital: {portfolio.capital}")
            print(f"📊 Posiciones: {list(portfolio.posiciones.keys())}")
            print("⏳ Entrenando...\n")

            time.sleep(config.CYCLE_TIME)

        except Exception as e:
            print(f"❌ ERROR CRÍTICO: {e}")
            time.sleep(10)

# =========================
# MAIN
# =========================
if __name__ == "__main__":

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)