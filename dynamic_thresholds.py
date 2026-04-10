import time
import config

class DynamicThresholdOptimizer:
    def __init__(self):
        self.last_optimization = 0
        self.optimal = {
            'rsi_min': config.RSI_MIN_BASE,
            'rsi_max': config.RSI_MAX_BASE,
            'vol_max': config.VOLATILIDAD_MAX_BASE,
            'vol_min': config.VOLATILIDAD_MIN_BASE,
            'score_min': config.SCORE_MINIMO_BASE,
        }
    
    def optimize(self, historical_data=None):
        if time.time() - self.last_optimization < config.OPTIMIZE_EVERY_HOURS * 3600:
            return self.optimal
        
        print("🔍 Optimización de umbrales (manteniendo valores base por ahora)")
        self.last_optimization = time.time()
        return self.optimal

optimizer = DynamicThresholdOptimizer()
