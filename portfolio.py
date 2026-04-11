import config
import time
import csv
import numpy as np
from exchange_connector import exchange

class Portfolio:
    def __init__(self):
        self.capital_inicial = config.CAPITAL_INICIAL
        self.capital = config.CAPITAL_INICIAL
        self.posiciones = {}
        self.historial = []
        self.last_trade = 0
        self.cooldown = config.COOLDOWN_BASE
        print(f"🚀 Capital inicial: ${self.capital_inicial} | Modo {'SIMULACIÓN' if config.SIMULATION_MODE else 'REAL'}")
        print(f"📊 Tamaños: Elite {config.TAMANO_ELITE*100}% | Buena {config.TAMANO_OPORTUNISTA_BUENA*100}%")
        print(f"🔄 Rotación flexible: Elite rota si peor posición tiene <20% ganancia")
        print(f"📈 Máximo de posiciones: {config.MAX_POSICIONES}")
    
    def capital_invertido(self):
        return sum(p["inversion"] for p in self.posiciones.values())
    
    def exposicion_actual(self):
        if self.capital_inicial == 0:
            return 0
        return self.capital_invertido() / self.capital
    
    def actualizar_cooldown(self):
        if len(self.historial) < 5:
            self.cooldown = config.COOLDOWN_BASE
            return
        ultimos = self.historial[-10:]
        winrate = sum(1 for t in ultimos if t["pnl"] > 0) / len(ultimos)
        if winrate < 0.4:
            self.cooldown = min(config.COOLDOWN_MAX, self.cooldown + 5)
        elif winrate > 0.6:
            self.cooldown = max(config.COOLDOWN_MIN, self.cooldown - 2)
        else:
            self.cooldown = config.COOLDOWN_BASE
    
    def puede_operar(self):
        return (time.time() - self.last_trade) > self.cooldown
    
    def obtener_grupo(self, symbol):
        for g, lista in config.CORRELACION.items():
            if symbol in lista:
                return g
        return None
    
    def correlacionado(self, symbol):
        grupo_nuevo = self.obtener_grupo(symbol)
        if grupo_nuevo is None:
            return False
        for s in self.posiciones.keys():
            grupo_existente = self.obtener_grupo(s)
            if grupo_existente == grupo_nuevo:
                print(f"   ⚠️ Correlación: {symbol} en grupo {grupo_nuevo} con {s}")
                return True
        return False
    
    def calcular_calidad_senal(self, prob, score):
        return (prob * 0.6) + ((score / 4) * 0.4)
    
    def evaluar_posiciones(self, precios):
        ranking = []
        for symbol, pos in self.posiciones.items():
            precio = precios.get(symbol)
            if precio is None:
                continue
            pnl = (precio - pos["entry"]) / pos["entry"]
            tiempo = time.time() - pos["tiempo"]
            calidad_pos = self.calcular_calidad_senal(pos.get("prob", 0), pos.get("score", 0))
            if pnl < -0.02:
                calidad_pos *= 0.5
            elif pnl > 0.05:
                calidad_pos *= 1.2
            if tiempo > 14400 and pnl < 0.01:
                calidad_pos *= 0.8
            ranking.append({
                "symbol": symbol,
                "pnl": pnl,
                "calidad": calidad_pos,
                "posicion": pos
            })
        ranking.sort(key=lambda x: x["calidad"])
        if ranking:
            peor = ranking[0]
            print(f"   📉 Peor posición: {peor['symbol']} | pnl {peor['pnl']*100:.2f}% | calidad {peor['calidad']:.2f}")
        return ranking
    
    def deberia_rotar(self, nueva_senal, ranking):
        if not ranking:
            return False
        peor = ranking[0]
        nueva_prob = nueva_senal.get("prob", 0)
        nuevo_score = nueva_senal.get("score", 0)
        nuevo_tipo = nueva_senal.get("tipo", "")
        es_elite = (nuevo_tipo == "elite") or (nueva_prob >= 0.70 and nuevo_score >= 3)
        nueva_calidad = self.calcular_calidad_senal(nueva_prob, nuevo_score)
        
        # Regla 1: Si es Elite y la peor posición tiene ganancia < 20% (muy flexible)
        if es_elite and peor["pnl"] < 0.20:
            print(f"   🔥 Rotación Elite: nueva calidad {nueva_calidad:.2f} vs peor calidad {peor['calidad']:.2f} (pnl {peor['pnl']*100:.1f}%)")
            return True
        
        # Regla 2: Calidad muy superior (umbral bajo)
        if nueva_calidad > peor["calidad"] + 0.10:
            print(f"   ⚡ Rotación por calidad: nueva {nueva_calidad:.2f} > peor {peor['calidad']:.2f} + 0.10")
            return True
        
        # Regla 3: Pérdida > 1% y señal decente
        if peor["pnl"] < -0.01 and nueva_calidad > 0.4:
            print(f"   📉 Rotación por pérdida: peor pnl {peor['pnl']*100:.1f}%")
            return True
        
        return False
    
    def get_tamano_por_calidad(self, tipo):
        if tipo == "elite":
            return config.TAMANO_ELITE
        elif tipo == "oportunista_buena":
            return config.TAMANO_OPORTUNISTA_BUENA
        else:
            return 0.05
    
    def comprar(self, symbol, precio, prob, score, tipo, precios=None, atr_stop=None, trailing_gap=None):
        # Cooldown
        if not self.puede_operar():
            tiempo_restante = self.cooldown - (time.time() - self.last_trade)
            if tiempo_restante > 0:
                print(f"   ⏱ Cooldown: esperar {round(tiempo_restante, 1)}s")
            return False
        
        if symbol in self.posiciones:
            print(f"   ⚠️ {symbol} ya está en posiciones")
            return False
        
        # ========== ROTACIÓN PRIORITARIA ==========
        if len(self.posiciones) >= config.MAX_POSICIONES:
            if precios is None:
                return False
            ranking = self.evaluar_posiciones(precios)
            if not ranking:
                return False
            nueva_senal = {"prob": prob, "score": score, "tipo": tipo}
            if self.deberia_rotar(nueva_senal, ranking):
                peor = ranking[0]
                print(f"   🔁 ROTANDO: sale {peor['symbol']} (pnl {round(peor['pnl']*100,1)}%, calidad {round(peor['calidad'],2)}) -> entra {symbol}")
                self.cerrar(peor['symbol'], precios[peor['symbol']])
            else:
                print(f"   ⚠️ Nueva señal no justifica rotación")
                return False
        
        # ========== CORRELACIÓN (después de posible rotación) ==========
        if self.correlacionado(symbol):
            print(f"   ⛔ Correlación evitada: {symbol}")
            return False
        
        # Tamaño de posición
        size_pct = self.get_tamano_por_calidad(tipo)
        capital_trade = self.capital * size_pct
        
        if capital_trade < 30:
            print(f"   ⚠️ Trade muy pequeño: ${round(capital_trade,2)} (mínimo $30)")
            return False
        
        nuevo_total = self.capital_invertido() + capital_trade
        limite = self.capital_inicial * config.USO_CAPITAL
        
        print(f"   💰 Capital: ${round(self.capital,2)} | Invertido: ${round(self.capital_invertido(),2)} | Nuevo: ${round(capital_trade,2)} ({round(size_pct*100)}%)")
        
        if nuevo_total > limite:
            print(f"   ⚠️ Límite de capital excedido")
            return False
        if capital_trade > self.capital:
            print(f"   ⚠️ Capital insuficiente")
            return False
        
        cantidad = capital_trade / precio
        
        if config.SIMULATION_MODE:
            precio_real = precio
            cantidad_real = cantidad
            capital_trade_real = capital_trade
        else:
            try:
                order = exchange.create_market_buy_order(symbol, cantidad)
                precio_real = order['price']
                cantidad_real = order['amount']
                capital_trade_real = cantidad_real * precio_real
            except Exception as e:
                print(f"   ❌ Error en orden real: {e}")
                return False
        
        stop_loss = atr_stop if atr_stop is not None else -0.02
        trailing_gap_used = trailing_gap if trailing_gap is not None else 0.015
        
        self.posiciones[symbol] = {
            "entry": precio_real,
            "cantidad": cantidad_real,
            "inversion": capital_trade_real,
            "max_precio": precio_real,
            "prob": prob,
            "score": score,
            "tipo": tipo,
            "trailing": False,
            "break_even": False,
            "tiempo": time.time(),
            "stop_loss_dinamico": stop_loss,
            "trailing_gap": trailing_gap_used
        }
        
        self.capital -= capital_trade_real
        self.last_trade = time.time()
        
        print(f"   ✅ COMPRA: {symbol} | ${round(capital_trade_real,2)} ({round(size_pct*100)}%) | {tipo} | prob {round(prob,2)}")
        return True
    
    def actualizar(self, precios):
        for symbol in list(self.posiciones.keys()):
            pos = self.posiciones[symbol]
            precio = precios.get(symbol)
            if precio is None:
                continue
            pnl = (precio - pos["entry"]) / pos["entry"]
            if precio > pos["max_precio"]:
                pos["max_precio"] = precio
            
            if pnl <= pos["stop_loss_dinamico"]:
                print(f"   🔴 Stop loss en {symbol}: pnl {round(pnl*100,1)}%")
                self.cerrar(symbol, precio)
                continue
            
            if pnl > 0.015:
                pos["break_even"] = True
            if pos["break_even"] and pnl <= 0:
                print(f"   🔴 Break even en {symbol}")
                self.cerrar(symbol, precio)
                continue
            
            if pnl > 0.02:
                pos["trailing"] = True
            if pos["trailing"]:
                stop = pos["max_precio"] * (1 - pos["trailing_gap"])
                if precio <= stop:
                    print(f"   🔴 Trailing stop en {symbol}")
                    self.cerrar(symbol, precio)
                    continue
    
    def cerrar(self, symbol, precio):
        pos = self.posiciones[symbol]
        valor = pos["cantidad"] * precio
        pnl = (precio - pos["entry"]) / pos["entry"]
        self.capital += valor
        trade = {
            "symbol": symbol,
            "pnl": round(pnl, 4),
            "capital": round(self.capital, 2),
            "entry": pos["entry"],
            "exit": precio,
            "tipo_senal": pos.get("tipo", "desconocido"),
            "prob_entrada": pos.get("prob", 0)
        }
        self.historial.append(trade)
        if not config.SIMULATION_MODE:
            try:
                exchange.create_market_sell_order(symbol, pos["cantidad"])
            except Exception as e:
                print(f"❌ Error en venta real: {e}")
        print(f"   🔴 VENTA: {symbol} | pnl {round(pnl*100,1)}% | Capital: ${round(self.capital,2)}")
        del self.posiciones[symbol]
    
    def guardar_resultados(self):
        try:
            fieldnames = ["symbol", "pnl", "capital", "entry", "exit", "tipo_senal", "prob_entrada"]
            with open("historial_trades.csv", "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in self.historial:
                    row = {k: t.get(k, "") for k in fieldnames}
                    writer.writerow(row)
        except Exception as e:
            print(f"Error guardando: {e}")
    
    def data(self):
        capital_actual = round(self.capital, 2)
        pnl = round(capital_actual - self.capital_inicial, 2)
        pnl_pct = round((pnl / self.capital_inicial) * 100, 2) if self.capital_inicial != 0 else 0
        return {
            "capital": capital_actual,
            "capital_inicial": self.capital_inicial,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "posiciones": self.posiciones,
            "historial": self.historial[-20:]
        }

portfolio = Portfolio()