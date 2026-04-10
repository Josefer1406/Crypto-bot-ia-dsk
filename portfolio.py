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
        print(f"📊 Tamaños: Elite {config.TAMANO_ELITE*100}% | Buena {config.TAMANO_OPORTUNISTA_BUENA*100}% | Regular {config.TAMANO_OPORTUNISTA_REGULAR*100}%")
    
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
    
    def peor_posicion(self, precios):
        peor_symbol = None
        peor_pnl = 999
        for symbol, pos in self.posiciones.items():
            precio = precios.get(symbol)
            if precio is None:
                continue
            pnl = (precio - pos["entry"]) / pos["entry"]
            if pnl < peor_pnl:
                peor_pnl = pnl
                peor_symbol = symbol
        return peor_symbol, peor_pnl
    
    def get_tamano_por_calidad(self, tipo, prob, score):
        """Retorna el porcentaje del capital a invertir según la calidad"""
        if tipo == "elite":
            return config.TAMANO_ELITE
        elif tipo == "oportunista_buena":
            return config.TAMANO_OPORTUNISTA_BUENA
        elif tipo == "oportunista_regular":
            return config.TAMANO_OPORTUNISTA_REGULAR
        else:
            # Fallback seguro
            return 0.03
    
    def comprar(self, symbol, precio, prob, score, tipo, precios=None, atr_stop=None, trailing_gap=None):
        # Verificar cooldown
        if not self.puede_operar():
            tiempo_restante = self.cooldown - (time.time() - self.last_trade)
            if tiempo_restante > 0:
                print(f"   ⏱ Cooldown: esperar {round(tiempo_restante, 1)}s")
            return False
        
        # Verificar si ya está en posiciones
        if symbol in self.posiciones:
            print(f"   ⚠️ {symbol} ya está en posiciones")
            return False
        
        # Verificar correlación
        if self.correlacionado(symbol):
            print(f"   ⛔ Correlación evitada: {symbol}")
            return False
        
        # Calcular tamaño según calidad
        size_pct = self.get_tamano_por_calidad(tipo, prob, score)
        capital_trade = self.capital * size_pct
        
        # Verificar límite mínimo de trade
        if capital_trade < 30:
            print(f"   ⚠️ Trade muy pequeño: ${round(capital_trade,2)} (mínimo $30)")
            return False
        
        # Verificar límite de capital total
        nuevo_total_invertido = self.capital_invertido() + capital_trade
        limite_maximo = self.capital_inicial * config.USO_CAPITAL
        
        print(f"   💰 Capital: ${round(self.capital,2)} | Invertido: ${round(self.capital_invertido(),2)} | Nuevo: ${round(capital_trade,2)} ({round(size_pct*100)}%)")
        
        if nuevo_total_invertido > limite_maximo:
            print(f"   ⚠️ Límite excedido: {round(nuevo_total_invertido,2)} > {round(limite_maximo,2)}")
            return False
        
        if capital_trade > self.capital:
            print(f"   ⚠️ Capital insuficiente: ${round(capital_trade,2)} > ${round(self.capital,2)}")
            return False
        
        # Si está lleno, intentar rotar
        if len(self.posiciones) >= config.MAX_POSICIONES:
            if precios is None:
                return False
            peor_symbol, peor_pnl = self.peor_posicion(precios)
            if peor_pnl >= 0:
                print(f"   ⚠️ No hay posiciones con pérdidas para rotar")
                return False
            if tipo != "elite" and prob < 0.70:
                print(f"   ⚠️ Solo Elite puede rotar con prob < 0.70")
                return False
            print(f"   🔁 ROTANDO: sale {peor_symbol} (pnl {round(peor_pnl,2)}) -> entra {symbol}")
            self.cerrar(peor_symbol, precios[peor_symbol])
        
        cantidad = capital_trade / precio
        
        # Ejecutar compra
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
            
            # Stop loss dinámico
            if pnl <= pos["stop_loss_dinamico"]:
                print(f"   🔴 Stop loss en {symbol}: pnl {round(pnl,4)}")
                self.cerrar(symbol, precio)
                continue
            
            # Break even después de +1.5%
            if pnl > 0.015:
                pos["break_even"] = True
            if pos["break_even"] and pnl <= 0:
                print(f"   🔴 Break even en {symbol}")
                self.cerrar(symbol, precio)
                continue
            
            # Trailing stop
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
            "pnl": float(round(pnl, 4)),
            "capital": float(round(self.capital, 2)),
            "tipo": "SELL",
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
        
        print(f"   🔴 VENTA: {symbol} | pnl {round(pnl,4)} | Capital: ${round(self.capital,2)}")
        del self.posiciones[symbol]
    
    def guardar_resultados(self):
        try:
            with open("historial_trades.csv", "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["symbol", "pnl", "capital", "entry", "exit", "tipo_senal", "prob_entrada"])
                writer.writeheader()
                for t in self.historial:
                    writer.writerow(t)
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
