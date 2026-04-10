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
        print(f"🚀 Capital inicial: {self.capital_inicial} | Modo {'SIMULACIÓN' if config.SIMULATION_MODE else 'REAL'}")
    
    def capital_invertido(self):
        return sum(p["inversion"] for p in self.posiciones.values())
    
    def exposicion_actual(self):
        if self.capital_inicial == 0:
            return 0
        return self.capital_invertido() / self.capital_inicial
    
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
        """Devuelve el grupo de correlación de un símbolo"""
        for g, lista in config.CORRELACION.items():
            if symbol in lista:
                return g
        return None
    
    def correlacionado(self, symbol):
        """Verifica si el símbolo está en el mismo grupo que alguna posición abierta"""
        grupo_nuevo = self.obtener_grupo(symbol)
        
        # Si no tiene grupo definido, no está correlacionado
        if grupo_nuevo is None:
            return False
        
        # Verificar si alguna posición abierta está en el mismo grupo
        for s in self.posiciones.keys():
            grupo_existente = self.obtener_grupo(s)
            if grupo_existente == grupo_nuevo:
                print(f"   ⚠️ Correlación: {symbol} está en grupo {grupo_nuevo} con {s}")
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
    
    def calcular_tamano_kelly(self, prob):
        if len(self.historial) > 20:
            recent = self.historial[-20:]
            winrate = sum(1 for t in recent if t["pnl"] > 0) / len(recent)
            avg_win = np.mean([t["pnl"] for t in recent if t["pnl"] > 0]) if winrate > 0 else 0
            avg_loss = abs(np.mean([t["pnl"] for t in recent if t["pnl"] <= 0])) if (1-winrate) > 0 else 1
            b = avg_win / avg_loss if avg_loss != 0 else 1
            kelly = (winrate * b - (1 - winrate)) / b
            kelly = max(0, min(kelly, 0.25))
        else:
            winrate_est = prob
            b = 1.5
            kelly = (winrate_est * b - (1 - winrate_est)) / b
            kelly = max(0, min(kelly, 0.25))
        return kelly * config.KELLY_FRACTION
    
    def comprar(self, symbol, precio, prob, score_nuevo=None, precios=None, atr_stop=None, trailing_gap=None):
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
        
        # Calcular espacios disponibles
        espacios_disponibles = config.MAX_POSICIONES - len(self.posiciones)
        print(f"   📊 Espacios disponibles: {espacios_disponibles} de {config.MAX_POSICIONES}")
        
        # Si no hay espacios, intentar rotar
        if espacios_disponibles == 0:
            if precios is None:
                return False
            peor_symbol, peor_pnl = self.peor_posicion(precios)
            if peor_pnl >= 0:
                print(f"   ⚠️ No hay posiciones con pérdidas para rotar (peor pnl: {round(peor_pnl,2)})")
                return False
            if prob < 0.70:
                print(f"   ⚠️ Probabilidad {prob} insuficiente para rotar (mínimo 0.70)")
                return False
            print(f"   🔁 ROTANDO: sale {peor_symbol} (pnl {round(peor_pnl,2)}) -> entra {symbol}")
            self.cerrar(peor_symbol, precios[peor_symbol])
            espacios_disponibles = 1
        
        # Calcular tamaño de posición
        kelly_size = self.calcular_tamano_kelly(prob)
        size = max(0.05, min(kelly_size, 0.25))
        capital_trade = self.capital_inicial * size
        
        # Verificar límite de capital
        nuevo_total_invertido = self.capital_invertido() + capital_trade
        limite_maximo = self.capital_inicial * config.USO_CAPITAL
        
        print(f"   💰 Capital disponible: ${round(self.capital,2)} | Invertido: ${round(self.capital_invertido(),2)} | Nuevo trade: ${round(capital_trade,2)}")
        
        if nuevo_total_invertido > limite_maximo:
            print(f"   ⚠️ Límite de capital excedido: {round(nuevo_total_invertido,2)} > {round(limite_maximo,2)}")
            return False
        
        if capital_trade > self.capital:
            print(f"   ⚠️ Capital insuficiente: necesita ${round(capital_trade,2)} pero tiene ${round(self.capital,2)}")
            return False
        
        cantidad = capital_trade / precio
        
        # Ejecutar compra (simulación)
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
                print(f"   ❌ Error en orden de compra real: {e}")
                return False
        
        stop_loss = atr_stop if atr_stop is not None else -0.02
        trailing_gap_used = trailing_gap if trailing_gap is not None else 0.015
        
        # REGISTRAR POSICIÓN ANTES DE RESTAR CAPITAL
        self.posiciones[symbol] = {
            "entry": precio_real,
            "cantidad": cantidad_real,
            "inversion": capital_trade_real,
            "max_precio": precio_real,
            "prob": prob,
            "trailing": False,
            "break_even": False,
            "tiempo": time.time(),
            "stop_loss_dinamico": stop_loss,
            "trailing_gap": trailing_gap_used
        }
        
        # RESTAR EL CAPITAL (ESTA ES LA LÍNEA QUE FALTABA)
        self.capital -= capital_trade_real
        
        self.last_trade = time.time()
        
        print(f"   ✅ COMPRA: {symbol} | ${capital_trade_real:.2f} | prob {round(prob,2)} | Capital restante: ${round(self.capital,2)}")
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
            
            # Stop loss
            if pnl <= pos["stop_loss_dinamico"]:
                print(f"   🔴 Stop loss en {symbol}: pnl {round(pnl,4)}")
                self.cerrar(symbol, precio)
                continue
            
            # Break even
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
        
        # Calcular PnL antes de actualizar capital
        pnl = (precio - pos["entry"]) / pos["entry"]
        
        # SUMAR EL CAPITAL DE VUELTA
        self.capital += valor
        
        trade = {
            "symbol": symbol,
            "pnl": float(round(pnl, 4)),
            "capital": float(round(self.capital, 2)),
            "tipo": "SELL",
            "entry": pos["entry"],
            "exit": precio
        }
        self.historial.append(trade)
        
        if not config.SIMULATION_MODE:
            try:
                exchange.create_market_sell_order(symbol, pos["cantidad"])
            except Exception as e:
                print(f"❌ Error en orden de venta real: {e}")
        
        print(f"   🔴 VENTA: {symbol} | pnl {round(pnl,4)} | Capital: ${round(self.capital,2)}")
        del self.posiciones[symbol]
    
    def guardar_resultados(self):
        try:
            with open("historial_trades.csv", "w", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["symbol", "pnl", "capital", "entry", "exit"])
                writer.writeheader()
                for t in self.historial:
                    writer.writerow(t)
        except Exception as e:
            print(f"Error guardando historial: {e}")
    
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
