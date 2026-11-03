import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

from universe import get_nifty50_symbols
from scanner import scan_nifty50, get_latest_scan, get_scan_history, get_stock_history
from analysis import enrich_indicators, candle_pattern_summary, indicator_summary
from storage import init_db

IST = ZoneInfo("Asia/Kolkata")
st.set_page_config(page_title="Market Intelligence Pro", page_icon="📈", layout="wide")
init_db()

st.title("📈 Market Intelligence Pro")
st.caption("Nifty 50 • Technical Analysis • Candle Patterns • RSI / MACD • Scan History")

with st.sidebar:
    st.header("Controls")
    interval = st.selectbox("Chart / scan timeframe", ["5m", "15m", "30m", "1h", "1d"], index=0)
    auto_scan = st.toggle("Market-hours auto scan", value=True)
    st.caption("Auto scan works only while this app process is awake.")
    st.caption("Market window: 09:15–15:30 IST")
    manual = st.button("🔄 Scan Nifty 50 now", type="primary", use_container_width=True)
    st.divider()
    st.write("Data source: Yahoo Finance (free, may be delayed/rate-limited)")
    st.write("Last local time:", datetime.now(IST).strftime("%d-%m-%Y %H:%M:%S"))

now = datetime.now(IST)
market_open = dtime(9,15) <= now.time() <= dtime(15,30) and now.weekday() < 5
if auto_scan:
    st_autorefresh(interval=60_000, key="mip_refresh")

# Scheduled polling: scan at first app run after open, then every 15 minutes.
if auto_scan and market_open:
    last_auto = st.session_state.get("last_auto_scan")
    due = last_auto is None or (now-last_auto).total_seconds() >= 900
    if due and not manual:
        manual = True
        st.session_state["last_auto_scan"] = now

if manual:
    with st.status("Nifty 50 scan running — stocks are processed one by one...", expanded=True) as status:
        progress = st.progress(0)
        msg = st.empty()
        result = scan_nifty50(interval=interval, progress_callback=lambda n,total,s: (progress.progress(n/total), msg.write(f"{n}/{total}: {s}")))
        status.update(label=f"Scan finished: {len(result)} stocks processed", state="complete")

latest = get_latest_scan()
if latest.empty:
    st.info("अभी scan history उपलब्ध नहीं है। 'Scan Nifty 50 now' दबाएँ या market-hours auto scan के लिए app चालू रखें।")
else:
    st.subheader("Latest Nifty 50 Scan")
    stamp = latest["Scan Time"].iloc[0] if "Scan Time" in latest else "Unknown"
    st.caption(f"Saved scan: {stamp} | Rows: {len(latest)} | Freshness depends on data provider")
    a,b,c = st.columns(3)
    a.metric("Stocks scanned", len(latest))
    b.metric("Bullish", int((latest["Signal"]=="BULLISH").sum()))
    c.metric("Bearish", int((latest["Signal"]=="BEARISH").sum()))
    good = latest[latest["Signal"].isin(["BULLISH","BEARISH"])]
    left,right = st.columns(2)
    with left:
        st.markdown("### 🟢 Top 10 Bullish")
        st.dataframe(latest[latest.Signal=="BULLISH"].sort_values("Bullish Score",ascending=False).head(10), use_container_width=True, hide_index=True)
    with right:
        st.markdown("### 🔴 Top 10 Bearish")
        st.dataframe(latest[latest.Signal=="BEARISH"].sort_values("Bearish Score",ascending=False).head(10), use_container_width=True, hide_index=True)
    st.markdown("### Complete scan")
    st.dataframe(latest, use_container_width=True, hide_index=True)
    st.download_button("Download latest scan CSV", latest.to_csv(index=False).encode("utf-8"), "nifty50_latest_scan.csv", "text/csv")

tabs = st.tabs(["📊 Chart Analysis", "🕯️ Candle Patterns", "📐 RSI & Indicators", "🗂️ Scan History", "ℹ️ About"])
with tabs[0]:
    symbols = get_nifty50_symbols()
    choice = st.selectbox("Select Nifty 50 stock", symbols, index=0 if symbols else None)
    if choice:
        raw = get_stock_history(choice, interval)
        if raw is None or raw.empty:
            st.warning("इस शेयर का डेटा अभी उपलब्ध नहीं है। कुछ समय बाद दोबारा प्रयास करें।")
        else:
            df = enrich_indicators(raw)
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name="Price"))
            for col in ["EMA9","EMA21","EMA50"]:
                if col in df: fig.add_trace(go.Scatter(x=df.index,y=df[col],name=col,mode="lines"))
            fig.update_layout(height=600, xaxis_rangeslider_visible=False, title=f"{choice} — {interval}")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df.tail(30).sort_index(ascending=False), use_container_width=True)
with tabs[1]:
    symbols = get_nifty50_symbols()
    choice2 = st.selectbox("Stock for candle analysis", symbols, key="candle_stock")
    if choice2:
        raw = get_stock_history(choice2, interval)
        if raw is not None and not raw.empty:
            df = enrich_indicators(raw)
            st.write(candle_pattern_summary(df))
            st.dataframe(df[["Open","High","Low","Close","Volume"]].tail(20).sort_index(ascending=False), use_container_width=True)
        else: st.warning("Data unavailable.")
with tabs[2]:
    symbols = get_nifty50_symbols()
    choice3 = st.selectbox("Stock for indicator analysis", symbols, key="indicator_stock")
    if choice3:
        raw = get_stock_history(choice3, interval)
        if raw is not None and not raw.empty:
            df = enrich_indicators(raw)
            st.dataframe(indicator_summary(df), use_container_width=True, hide_index=True)
            st.line_chart(df[["RSI14","MACD","MACD_Signal"]].tail(100))
        else: st.warning("Data unavailable.")
with tabs[3]:
    hist = get_scan_history(limit=100)
    if hist.empty: st.info("No saved scan history yet.")
    else:
        st.dataframe(hist, use_container_width=True, hide_index=True)
        st.download_button("Download scan history CSV", hist.to_csv(index=False).encode(), "mip_scan_history.csv", "text/csv")
with tabs[4]:
    st.markdown("""
**Important limitations**
- Yahoo Finance is an unofficial free data source; availability, delay and rate limits can vary.
- Automatic scans run only while the Streamlit process is awake. Render Free may sleep when idle; reliable 09:15 scheduling requires an always-on host or external scheduler.
- Technical signals are probability-style indicators, not guaranteed predictions or investment advice.
- A WAIT / NO TRADE result is intentional when evidence is mixed or data is missing.
""")
