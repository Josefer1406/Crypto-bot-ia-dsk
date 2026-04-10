import ccxt
import config

class ExchangeConnector:
    def __init__(self):
        self.name = config.EXCHANGE_NAME
        self.simulation = config.SIMULATION_MODE
        
        if self.simulation:
            # En simulación, NO usamos API keys (solo datos públicos)
            print("🔁 MODO SIMULACIÓN - Usando conexión pública sin API keys")
            if self.name == "okx":
                self.exchange = ccxt.okx({
                    'enableRateLimit': True,
                })
            elif self.name == "binance":
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                })
            else:
                raise ValueError(f"Exchange {self.name} no soportado")
        else:
            # Modo real: usar API keys
            if self.name == "okx":
                self.exchange = ccxt.okx({
                    'apiKey': config.OKX_API_KEY,
                    'secret': config.OKX_SECRET_KEY,
                    'password': config.OKX_PASSPHRASE,
                    'enableRateLimit': True,
                })
            elif self.name == "binance":
                self.exchange = ccxt.binance({
                    'apiKey': config.BINANCE_API_KEY,
                    'secret': config.BINANCE_SECRET_KEY,
                    'enableRateLimit': True,
                })
            else:
                raise ValueError(f"Exchange {self.name} no soportado")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=150):
        # En simulación, si hay error de autenticación, reintentamos sin keys (ya lo estamos haciendo)
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    def create_market_buy_order(self, symbol, amount):
        if self.simulation:
            print(f"🔁 [SIM] Comprar {amount} de {symbol}")
            ticker = self.exchange.fetch_ticker(symbol)
            return {'price': ticker['last'], 'amount': amount, 'cost': amount * ticker['last']}
        else:
            return self.exchange.create_market_buy_order(symbol, amount)
    
    def create_market_sell_order(self, symbol, amount):
        if self.simulation:
            print(f"🔁 [SIM] Vender {amount} de {symbol}")
            ticker = self.exchange.fetch_ticker(symbol)
            return {'price': ticker['last'], 'amount': amount, 'cost': amount * ticker['last']}
        else:
            return self.exchange.create_market_sell_order(symbol, amount)
    
    def fetch_ticker(self, symbol):
        return self.exchange.fetch_ticker(symbol)
    
    def fetch_balance(self):
        if self.simulation:
            return {'total': {'USDT': config.CAPITAL_INICIAL}}
        else:
            return self.exchange.fetch_balance()

exchange = ExchangeConnector()