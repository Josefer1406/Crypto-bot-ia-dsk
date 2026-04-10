import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Bot Dashboard", layout="wide")
st.title("📊 Bot Cuantitativo con IA")

url = st.secrets.get("BOT_URL", "https://tuservicio.railway.app/data")

placeholder = st.empty()

while True:
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            col1.metric("Capital Actual", f"${data['capital']:,.2f}")
            col2.metric("PnL", f"${data['pnl']:,.2f}")
            col3.metric("PnL %", f"{data['pnl_pct']:.2f}%")
            
            st.subheader("Posiciones Abiertas")
            if data['posiciones']:
                df_pos = pd.DataFrame(data['posiciones']).T
                st.dataframe(df_pos)
            else:
                st.info("Sin posiciones abiertas")
            
            st.subheader("Últimos Trades")
            if data['historial']:
                df_hist = pd.DataFrame(data['historial'])
                st.dataframe(df_hist.tail(10))
        
        time.sleep(5)
    except:
        st.error("Error conectando al bot")
        time.sleep(10)
