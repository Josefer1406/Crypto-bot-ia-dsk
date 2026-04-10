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
    
    # Elite: alta calidad
    if prob >= 0.70 and score >= 3:
        return "elite"
    
    # Oportunista: calidad media (bajado a 0.50 para más señales)
    if prob >= 0.50 and score >= 2:
        return "oportunista"
    
    return None

def bot():
    print("🚀 BOT HEDGE FUND CON IA - MODO", "SIMULACIÓN" if config.SIMULATION_MODE else "REAL")
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
                data["score_final"] = score_institucional(data)
                ranking_total.append(data)
            
            portfolio.actualizar(precios)
            
            if not ranking_total:
                print("⛔ No hay activos válidos")
                time.sleep(config.CYCLE_TIME)
                continue
            
            ranking_total.sort(key=lambda x: x["score_final"], reverse=True)
            universo = ranking_total[:8]
            elite = [a for a in universo if clasificar_trade(a) == "elite"]
            oportunistas = [a for a in universo if clasificar_trade(a) == "oportunista"]
            
            espacios = config.MAX_POSICIONES - len(portfolio.posiciones)
            print(f"   📊 Espacios libres: {espacios} | Elite: {len(elite)} | Oportunistas: {len(oportunistas)}")
            
            if espacios > 0:
                seleccion = elite[:espacios]
                if not seleccion:
                    seleccion = oportunistas[:espacios]
            else:
                candidatos = elite if elite else oportunistas
                if not candidatos:
                    print("⛔ Sin candidatos para rotar")
                    time.sleep(config.CYCLE_TIME)
                    continue
                seleccion = [candidatos[0]]
            
            ejecutados = 0
            for asset in seleccion:
                # Verificar si ya está en posiciones ANTES de comprar
                if asset["symbol"] in portfolio.posiciones:
                    print(f"   ⚠️ {asset['symbol']} ya está en posiciones, saltando")
                    continue
                
                ejecutado = portfolio.comprar(
                    asset["symbol"],
                    asset["precio"],
                    asset["prob"],
                    asset["score_final"],
                    precios,
                    atr_stop=asset.get("stop_loss_dinamico"),
                    trailing_gap=asset.get("trailing_gap")
                )
                if ejecutado:
                    ejecutados += 1
                    print(f"   🟢 TRADE EJECUTADO: {asset['symbol']} | prob {round(asset['prob'],2)} | score {round(asset['score_final'],2)}")
            
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
            
            print(f"💰 Capital: {round(portfolio.capital,2)}")
            print(f"📊 Posiciones: {list(portfolio.posiciones.keys())}")
            print(f"🌐 Universo activo: {len(universo)}")
            print(f"🔥 Elite: {len(elite)} | Oportunistas: {len(oportunistas)}")
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
