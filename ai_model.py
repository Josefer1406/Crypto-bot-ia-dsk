import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os
import config

MODEL_PATH = "ai_model.pkl"
SCALER_PATH = "scaler.pkl"

class AdaptiveProbabilityModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.load()
    
    def extract_features(self, df):
        last = df.iloc[-1]
        features = {
            'ema20_ema50_diff': (last['ema20'] - last['ema50']) / last['close'],
            'price_vs_ema20': (last['close'] - last['ema20']) / last['close'],
            'rsi': last['rsi'] / 100.0,
            'volatility': df['returns'].std(),
            'momentum_1': df['returns'].iloc[-1],
            'momentum_5': df['returns'].iloc[-5:].mean(),
        }
        return np.array(list(features.values())).reshape(1, -1)
    
    def train(self, historical_trades, historical_data):
        if len(historical_trades) < 30:
            print("⚠️ No hay suficientes trades para entrenar IA")
            return
        X = np.array([t['features'] for t in historical_trades])
        y = np.array([t['success'] for t in historical_trades])
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.model = LogisticRegression(C=1.0, class_weight='balanced')
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self.save()
        print(f"🧠 Modelo IA entrenado con {len(historical_trades)} trades")
    
    def predict_probability(self, df):
        if not self.is_trained or self.model is None:
            return None
        features = self.extract_features(df)
        features_scaled = self.scaler.transform(features)
        prob = self.model.predict_proba(features_scaled)[0][1]
        return float(prob)
    
    def save(self):
        if self.model:
            joblib.dump(self.model, MODEL_PATH)
            joblib.dump(self.scaler, SCALER_PATH)
    
    def load(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.is_trained = True
            print("📀 Modelo IA cargado desde disco")

ai_model = AdaptiveProbabilityModel()
