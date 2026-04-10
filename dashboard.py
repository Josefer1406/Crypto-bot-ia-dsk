import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("📊 QUANT DASHBOARD INSTITUCIONAL")

# 🔗 URL API
url = "https://data-analysis-project-production.up.railway.app/data"

try:
    df = pd.read_json(url)

    # =========================
    # VALIDACIÓN
    # =========================
    if df.empty:
        st.warning("⚠️ No hay datos aún")
        st.stop()

    # =========================
    # LIMPIEZA
    # =========================
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.sort_values("fecha")

    df["precio"] = df["precio"].astype(float)
    df["size"] = df["size"].astype(float)
    df["pnl"] = df["pnl"].astype(float)
    df["capital"] = df["capital"].astype(float)

    # =========================
    # SEPARAR TRADES
    # =========================
    buys = df[df["tipo"] == "BUY"]
    sells = df[df["tipo"] == "SELL"]

    # =========================
    # CAPITAL CURVE
    # =========================
    capital_curve = df["capital"]

    capital_actual = capital_curve.iloc[-1]
    capital_inicial = capital_curve.iloc[0]

    pnl_total = capital_actual - capital_inicial

    # =========================
    # WIN RATE
    # =========================
    if len(sells) > 0:
        winrate = len(sells[sells["pnl"] > 0]) / len(sells)
    else:
        winrate = 0

    # =========================
    # DRAWDOWN
    # =========================
    roll_max = capital_curve.cummax()
    drawdown = (capital_curve - roll_max) / roll_max

    # =========================
    # SHARPE
    # =========================
    returns = capital_curve.pct_change().dropna()

    if len(returns) > 1 and returns.std() != 0:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    else:
        sharpe = 0

    # =========================
    # METRICAS
    # =========================
    st.subheader("📈 Métricas principales")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Capital Inicial", round(capital_inicial, 2))
    col2.metric("Capital Actual", round(capital_actual, 2))
    col3.metric("PnL Total", round(pnl_total, 2))
    col4.metric("Win Rate %", round(winrate * 100, 2))

    col5, col6 = st.columns(2)

    col5.metric("Drawdown %", round(drawdown.min() * 100, 2))
    col6.metric("Sharpe", round(sharpe, 2))

    # =========================
    # GRAFICOS
    # =========================
    st.subheader("💰 Curva de Capital")
    st.line_chart(capital_curve)

    st.subheader("📉 Drawdown")
    st.area_chart(drawdown)

    # =========================
    # TRADES
    # =========================
    st.subheader("📋 Historial de Trades")

    st.dataframe(df, use_container_width=True)

    # =========================
    # DEBUG
    # =========================
    with st.expander("🔍 Debug"):
        st.write("Total trades:", len(df))
        st.write("BUY:", len(buys))
        st.write("SELL:", len(sells))

except Exception as e:
    st.error(f"❌ Error cargando datos: {e}")