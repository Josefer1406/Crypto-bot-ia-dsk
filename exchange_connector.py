import ccxt
import config

class ExchangeConnector:
    def __init__(self):
        self.name = config.EXCHANGE_NAME
        self.simulation = config.SIMULATION_MODE
        
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
        
        if self.simulation:
            print("🔁 MODO SIMULACIÓN - No se enviarán órdenes reales")
    
    def fetch_ohlcv(self, symbol, timeframe, limit=150):
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
