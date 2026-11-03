import requests
import pandas as pd
from io import StringIO
import streamlit as st

NIFTY50_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
# Fallback is a practical backup list; official CSV is preferred and may change over time.
FALLBACK = """ADANIENT,ADANIPORTS,APOLLOHOSP,ASIANPAINT,AXISBANK,BAJAJ-AUTO,BAJFINANCE,BAJAJFINSV,BEL,BPCL,BHARTIARTL,BOSCHLTD,BRITANNIA,CIPLA,COALINDIA,DRREDDY,EICHERMOT,ETERNAL,GRASIM,HCLTECH,HDFCBANK,HDFCLIFE,HINDALCO,HINDUNILVR,ICICIBANK,INDUSINDBK,INFY,ITC,JIOFIN,JSWSTEEL,KOTAKBANK,LT,M&M,MARUTI,NESTLEIND,NTPC,ONGC,POWERGRID,RELIANCE,SBILIFE,SBIN,SHRIRAMFIN,SUNPHARMA,TATACONSUM,TATASTEEL,TCS,TECHM,TITAN,TRENT,ULTRACEMCO,WIPRO"""
@st.cache_data(ttl=3600)
def get_nifty50_symbols():
    headers={"User-Agent":"Mozilla/5.0","Accept":"text/csv,*/*","Referer":"https://www.niftyindices.com/"}
    try:
        r=requests.get(NIFTY50_URL,headers=headers,timeout=15); r.raise_for_status()
        df=pd.read_csv(StringIO(r.text))
        if "Symbol" not in df.columns: raise ValueError("CSV Symbol column missing")
        syms=sorted(df["Symbol"].dropna().astype(str).str.strip().str.upper().unique().tolist())
        if len(syms)>=45: return syms
    except Exception:
        pass
    return sorted(FALLBACK.split(","))
