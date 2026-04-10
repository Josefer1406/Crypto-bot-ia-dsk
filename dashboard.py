import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Crypto Bot Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🤖 Crypto Trading Bot - Hedge Fund Dashboard")
st.markdown("---")

# URL del bot en Railway (CAMBIAR POR TU URL REAL)
# Ejemplo: "https://crypto-bot-ia-dsk.up.railway.app/data"
BOT_URL = st.secrets.get("BOT_URL", "https://crypto-bot-ia-dsk.up.railway.app/data")

# Sidebar con información
with st.sidebar:
    st.header("⚙️ Configuración")
    st.write(f"📡 **Bot URL:** {BOT_URL}")
    st.write(f"🕐 **Última actualización:** {datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    
    # Parámetros del bot (hardcodeados según config.py)
    st.header("📊 Parámetros del Bot")
    st.metric("Capital Inicial", "$1,000")
    st.metric("Máx. Posiciones", "3")
    st.metric("Tamaño Elite", "15%")
    st.metric("Tamaño Buena", "10%")
    st.metric("Tamaño Regular", "5%")
    st.metric("Cooldown Base", "20s")
    st.metric("Stop Loss Máx", "5%")
    
    st.markdown("---")
    st.caption("Dashboard actualizado automáticamente cada 5 segundos")

# Función para obtener datos del bot
@st.cache_data(ttl=5)
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

# Placeholder para actualización automática
placeholder = st.empty()

while True:
    data = fetch_bot_data()
    
    if data:
        with placeholder.container():
            # ========== MÉTRICAS PRINCIPALES ==========
            st.subheader("📈 Resumen de Rendimiento")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            capital_actual = data.get("capital", 0)
            capital_inicial = data.get("capital_inicial", 1000)
            pnl = data.get("pnl", 0)
            pnl_pct = data.get("pnl_pct", 0)
            
            col1.metric(
                "💰 Capital Actual", 
                f"${capital_actual:,.2f}",
                delta=f"${pnl:,.2f}"
            )
            col2.metric(
                "📊 PnL Total", 
                f"${pnl:,.2f}",
                delta=f"{pnl_pct:.2f}%"
            )
            col3.metric(
                "🎯 Winrate", 
                "Calculando...",
                help="Se mostrará después de varios trades"
            )
            col4.metric(
                "📈 Sharpe Ratio", 
                "N/A",
                help="Requiere historial de trades"
            )
            col5.metric(
                "📉 Max Drawdown", 
                "0%",
                help="Máxima caída desde el pico"
            )
            
            st.markdown("---")
            
            # ========== POSICIONES ABIERTAS ==========
            st.subheader("🔓 Posiciones Abiertas")
            posiciones = data.get("posiciones", {})
            
            if posiciones:
                pos_data = []
                for symbol, pos in posiciones.items():
                    entry = pos.get("entry", 0)
                    cantidad = pos.get("cantidad", 0)
                    inversion = pos.get("inversion", 0)
                    prob = pos.get("prob", 0)
                    score = pos.get("score", 0)
                    tipo = pos.get("tipo", "N/A")
                    pnl_actual = "Pendiente"
                    
                    pos_data.append({
                        "Símbolo": symbol,
                        "Entry": f"${entry:.4f}",
                        "Cantidad": f"{cantidad:.6f}",
                        "Inversión": f"${inversion:.2f}",
                        "Probabilidad": f"{prob:.1%}",
                        "Score": score,
                        "Tipo": tipo,
                        "PnL": pnl_actual
                    })
                
                df_pos = pd.DataFrame(pos_data)
                st.dataframe(df_pos, use_container_width=True)
            else:
                st.info("📭 No hay posiciones abiertas en este momento")
            
            st.markdown("---")
            
            # ========== HISTORIAL DE TRADES ==========
            st.subheader("📜 Historial de Trades")
            historial = data.get("historial", [])
            
            if historial:
                # Invertir para mostrar más recientes primero
                historial_reciente = list(reversed(historial))
                
                hist_data = []
                for trade in historial_reciente:
                    hist_data.append({
                        "Fecha": "Reciente",
                        "Símbolo": trade.get("symbol", "N/A"),
                        "PnL": f"{trade.get('pnl', 0)*100:.2f}%",
                        "Capital": f"${trade.get('capital', 0):,.2f}",
                        "Entry": f"${trade.get('entry', 0):.4f}",
                        "Exit": f"${trade.get('exit', 0):.4f}",
                        "Tipo Señal": trade.get("tipo_senal", "N/A"),
                        "Prob Entrada": f"{trade.get('prob_entrada', 0):.1%}"
                    })
                
                df_hist = pd.DataFrame(hist_data)
                st.dataframe(df_hist, use_container_width=True)
                
                # ========== ESTADÍSTICAS DE TRADES ==========
                st.subheader("📊 Estadísticas de Trading")
                
                # Calcular estadísticas
                trades_cerrados = [t for t in historial if t.get("tipo") == "SELL"]
                if trades_cerrados:
                    pnls = [t.get("pnl", 0) for t in trades_cerrados]
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
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Profit Factor", f"{profit_factor:.2f}")
                    col2.metric("Trades Totales", len(pnls))
                    
                    # ========== GRÁFICO DE DISTRIBUCIÓN ==========
                    st.subheader("📉 Distribución de PnL")
                    
                    fig_dist = px.histogram(
                        x=[p*100 for p in pnls],
                        nbins=20,
                        title="Distribución de Resultados por Trade",
                        labels={"x": "PnL (%)", "y": "Frecuencia"}
                    )
                    fig_dist.add_vline(x=0, line_dash="dash", line_color="red")
                    st.plotly_chart(fig_dist, use_container_width=True)
                    
                    # ========== CURVA DE EQUITY ==========
                    st.subheader("📈 Curva de Equity")
                    
                    # Construir curva de equity
                    equity_curve = []
                    capital_acumulado = capital_inicial
                    equity_curve.append(capital_acumulado)
                    
                    for trade in trades_cerrados:
                        capital_acumulado = trade.get("capital", capital_acumulado)
                        equity_curve.append(capital_acumulado)
                    
                    fig_equity = go.Figure()
                    fig_equity.add_trace(go.Scatter(
                        y=equity_curve,
                        mode="lines",
                        name="Capital",
                        line=dict(color="green", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(0,255,0,0.1)"
                    ))
                    fig_equity.add_hline(y=capital_inicial, line_dash="dash", line_color="gray", annotation_text="Capital Inicial")
                    fig_equity.update_layout(
                        title="Evolución del Capital",
                        xaxis_title="Número de Trade",
                        yaxis_title="Capital ($)",
                        height=400
                    )
                    st.plotly_chart(fig_equity, use_container_width=True)
                    
                else:
                    st.info("📊 Esperando primeros trades para mostrar estadísticas")
            else:
                st.info("📭 No hay historial de trades aún")
            
            # ========== INDICADORES DE RIESGO ==========
            st.subheader("⚠️ Indicadores de Riesgo")
            
            col1, col2, col3 = st.columns(3)
            
            # Calcular drawdown
            if historial and trades_cerrados:
                capitales = [capital_inicial] + [t.get("capital", 0) for t in trades_cerrados]
                peak = capitales[0]
                max_drawdown = 0
                for cap in capitales:
                    if cap > peak:
                        peak = cap
                    dd = (peak - cap) / peak * 100
                    if dd > max_drawdown:
                        max_drawdown = dd
                
                col1.metric("Drawdown Máximo", f"{max_drawdown:.2f}%")
                col2.metric("Ratio Sharpe", "N/A", help="Requiere datos diarios")
                col3.metric("Ratio Calmar", "N/A", help="Retorno / Drawdown")
            else:
                col1.metric("Drawdown Máximo", "0%")
                col2.metric("Ratio Sharpe", "N/A")
                col3.metric("Ratio Calmar", "N/A")
            
            # ========== ÚLTIMA ACTUALIZACIÓN ==========
            st.markdown("---")
            st.caption(f"🔄 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        with placeholder.container():
            st.error("❌ No se pudo conectar al bot. Verifica que esté corriendo en Railway.")
            st.write(f"URL intentada: {BOT_URL}")
    
    # Esperar 5 segundos antes de actualizar
    time.sleep(5)
