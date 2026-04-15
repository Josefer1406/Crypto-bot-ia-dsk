import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Crypto Bot Dashboard", layout="wide")
st.title("🤖 Crypto Trading Bot - Hedge Fund Dashboard")
st.markdown("---")

st_autorefresh(interval=10000, key="dashboard_auto_refresh")

BOT_URL = st.secrets.get("BOT_URL", "https://crypto-bot-ia-dsk-production.up.railway.app/data")

@st.cache_data(ttl=10)
def fetch_bot_data():
    try:
        response = requests.get(BOT_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error conectando al bot: {e}")
        return None

data = fetch_bot_data()

if data:
    # Métricas principales
    st.subheader("📈 Resumen de Rendimiento")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Capital Actual", f"${data.get('capital',0):,.2f}", delta=f"${data.get('pnl',0):,.2f}")
    col2.metric("📊 PnL Total", f"${data.get('pnl',0):,.2f}", delta=f"{data.get('pnl_pct',0):.2f}%")
    
    historial = data.get("historial", [])
    # Filtrar solo los trades que tienen 'tipo_senal' (las ventas) o directamente todos
    trades_cerrados = [t for t in historial if t.get("exit") is not None]  # todos tienen exit si son ventas
    if trades_cerrados:
        ganadores = sum(1 for t in trades_cerrados if t.get("pnl", 0) > 0)
        winrate = (ganadores / len(trades_cerrados)) * 100
        col3.metric("🎯 Winrate", f"{winrate:.1f}%")
    else:
        col3.metric("🎯 Winrate", "0%")
    col4.metric("📈 Sharpe Ratio", "N/A")
    col5.metric("📉 Max Drawdown", f"{data.get('max_drawdown',0):.1f}%")
    st.markdown("---")
    
    # Posiciones abiertas
    st.subheader("🔓 Posiciones Abiertas")
    posiciones = data.get("posiciones", {})
    if posiciones:
        pos_data = []
        for symbol, pos in posiciones.items():
            pos_data.append({
                "Símbolo": symbol,
                "Entry": f"${pos.get('entry',0):.4f}",
                "Cantidad": f"{pos.get('cantidad',0):.6f}",
                "Inversión": f"${pos.get('inversion',0):.2f}",
                "Probabilidad": f"{pos.get('prob',0):.1%}",
                "Score": pos.get('score',0),
                "Tipo": pos.get('tipo', 'N/A')
            })
        st.dataframe(pd.DataFrame(pos_data), use_container_width=True)
    else:
        st.info("📭 No hay posiciones abiertas")
    st.markdown("---")
    
    # Historial de trades (ventas)
    st.subheader("📜 Historial de Trades")
    if trades_cerrados:
        # Mostrar últimos 20 trades en orden inverso (más reciente primero)
        df_trades = pd.DataFrame(trades_cerrados[-20:][::-1])
        df_trades["pnl_pct"] = df_trades["pnl"] * 100
        df_trades["entry"] = df_trades["entry"].apply(lambda x: f"${x:.4f}")
        df_trades["exit"] = df_trades["exit"].apply(lambda x: f"${x:.4f}")
        df_trades["pnl_pct"] = df_trades["pnl_pct"].apply(lambda x: f"{x:.2f}%")
        # Seleccionar columnas relevantes
        columnas = ["symbol", "pnl_pct", "capital", "entry", "exit", "tipo_senal", "prob_entrada"]
        st.dataframe(df_trades[columnas], use_container_width=True)
        
        # Estadísticas
        st.subheader("📊 Estadísticas de Trading")
        pnls = [t["pnl"] for t in trades_cerrados]
        ganadores = [p for p in pnls if p > 0]
        perdedores = [p for p in pnls if p <= 0]
        winrate = len(ganadores) / len(pnls) * 100 if pnls else 0
        avg_win = sum(ganadores) / len(ganadores) * 100 if ganadores else 0
        avg_loss = sum(perdedores) / len(perdedores) * 100 if perdedores else 0
        profit_factor = abs(sum(ganadores) / sum(perdedores)) if perdedores and sum(perdedores) != 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", len(pnls))
        col2.metric("Winrate", f"{winrate:.1f}%")
        col3.metric("Avg Ganador", f"{avg_win:.2f}%")
        col4.metric("Avg Perdedor", f"{avg_loss:.2f}%")
        
        # Gráfico distribución
        fig_dist = px.histogram(x=[p*100 for p in pnls], nbins=20, title="Distribución de PnL por Trade", labels={"x": "PnL (%)", "y": "Frecuencia"})
        fig_dist.add_vline(x=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Curva de equity
        capital_inicial = data.get("capital_inicial", 1000)
        equity_curve = [capital_inicial]
        for trade in trades_cerrados:
            equity_curve.append(trade.get("capital", equity_curve[-1]))
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(y=equity_curve, mode="lines", name="Capital", line=dict(color="green", width=2), fill="tozeroy", fillcolor="rgba(0,255,0,0.1)"))
        fig_equity.add_hline(y=capital_inicial, line_dash="dash", line_color="gray")
        fig_equity.update_layout(title="Evolución del Capital", xaxis_title="Número de Trade", yaxis_title="Capital ($)")
        st.plotly_chart(fig_equity, use_container_width=True)
    else:
        st.info("📭 Aún no hay trades cerrados. Esperando a que el bot cierre posiciones.")
    
    # Riesgo
    st.subheader("⚠️ Indicadores de Riesgo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Drawdown Máximo", f"{data.get('max_drawdown',0):.2f}%")
    col2.metric("Ratio Sharpe", "N/A")
    col3.metric("Ratio Calmar", "N/A")
    
    st.caption(f"🔄 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.error("❌ No se pudo conectar al bot. Verifica que esté corriendo en Railway.")