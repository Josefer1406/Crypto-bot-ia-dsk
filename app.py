from flask import Flask, jsonify
import threading
import time
import config
from services.scanner import analizar
from portfolio import portfolio
from ai_model import ai_model
from dynamic_thresholds import optimizer

app = Flask(__name__)

def score_institucional(asset):
    prob = asset["prob"]
    score = asset["score"]
    s = (prob * 0.6) + ((score / 4) * 0.4)
    if prob > 0.85:
        s += 0.1
    return s

def clasificar_trade(asset):
    prob = asset["prob"]
    score = asset["score"]
    
    if prob >= 0.75 and score >= 3:
        return "elite"
    if prob >= 0.65 and score >= 2:
        return "oportunista_buena"
    return None

def bot():
    print("🚀 BOT HEDGE FUND CON IA - MODO", "SIMULACIÓN" if config.SIMULATION_MODE else "REAL")
    print("📊 Clasificación: Elite (12%) | Buena (8%)")
    print("🎯 Prob mín: Elite 0.75, Buena 0.65 | Score mín: Elite 3, Buena 2")
    contador = 0
    ultimo_reentreno = 0
    
    while True:
        try:
            contador += 1
            print("\n🔎 Analizando mercado...")
            ranking_total = []
            precios = {}
            
            for symbol in config.CRYPTOS:
                data = analizar(symbol)
                if data is None:
                    continue
                precios[symbol] = data["precio"]
                tipo = clasificar_trade(data)
                if tipo is None:
                    continue
                data["tipo"] = tipo
                data["score_final"] = score_institucional(data)
                ranking_total.append(data)
            
            portfolio.actualizar(precios)
            
            if not ranking_total:
                print("⛔ No hay activos válidos")
                time.sleep(config.CYCLE_TIME)
                continue
            
            ranking_total.sort(key=lambda x: x["score_final"], reverse=True)
            universo = ranking_total[:10]
            
            elite = [a for a in universo if a.get("tipo") == "elite"]
            buenas = [a for a in universo if a.get("tipo") == "oportunista_buena"]
            
            espacios = config.MAX_POSICIONES - len(portfolio.posiciones)
            print(f"   📊 Espacios: {espacios} | Elite: {len(elite)} | Buenas: {len(buenas)}")
            
            # Selección de candidatos
            seleccion = []
            if espacios > 0:
                # Hay espacio, tomar las mejores (que no estén ya en posiciones)
                candidatos = [a for a in (elite + buenas) if a["symbol"] not in portfolio.posiciones]
                seleccion = candidatos[:espacios]
            else:
                # No hay espacio, evaluar la mejor señal para posible rotación (que no esté ya en posiciones)
                candidatos_validos = [a for a in (elite + buenas) if a["symbol"] not in portfolio.posiciones]
                if candidatos_validos:
                    mejor_candidato = candidatos_validos[0]  # el mejor por score_final
                    print(f"   🔄 Evaluando rotación con {mejor_candidato['symbol']} ({mejor_candidato['tipo']})")
                    seleccion = [mejor_candidato]
            
            if not seleccion:
                print("⛔ Sin candidatos para operar")
                time.sleep(config.CYCLE_TIME)
                continue
            
            ejecutados = 0
            for asset in seleccion:
                ejecutado = portfolio.comprar(
                    asset["symbol"],
                    asset["precio"],
                    asset["prob"],
                    asset["score"],
                    asset.get("tipo"),
                    precios,
                    atr_stop=asset.get("stop_loss_dinamico"),
                    trailing_gap=asset.get("trailing_gap")
                )
                if ejecutado:
                    ejecutados += 1
                    print(f"   🟢 TRADE EJECUTADO: {asset['symbol']} | {asset['tipo']} | prob {round(asset['prob'],2)}")
                else:
                    # Si no se ejecutó, puede ser porque la rotación no fue posible
                    pass
            
            if ejecutados == 0:
                print("⛔ No se ejecutaron trades")
            
            portfolio.actualizar_cooldown()
            
            if contador % 20 == 0:
                portfolio.guardar_resultados()
                print("💾 Resultados guardados")
            
            if len(portfolio.historial) >= config.RETRAIN_EVERY_TRADES and (time.time() - ultimo_reentreno > 3600):
                print("🧠 Reentrenamiento de IA pendiente")
                ultimo_reentreno = time.time()
            
            optimizer.optimize()
            
            print(f"💰 Capital: ${round(portfolio.capital,2)}")
            print(f"📊 Posiciones: {list(portfolio.posiciones.keys())}")
            print(f"🌐 Universo activo: {len(universo)}")
            print(f"🔥 Elite: {len(elite)} | Buenas: {len(buenas)}")
            print(f"⏱ Cooldown: {portfolio.cooldown}s")
            
            time.sleep(config.CYCLE_TIME)
        
        except Exception as e:
            print(f"❌ ERROR BOT: {e}")
            time.sleep(5)

@app.route("/data")
def data():
    return jsonify(portfolio.data())

if __name__ == "__main__":
    threading.Thread(target=bot).start()
    app.run(host="0.0.0.0", port=8080)