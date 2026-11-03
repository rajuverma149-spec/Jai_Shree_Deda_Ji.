import time
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf
from universe import get_nifty50_symbols
from analysis import enrich_indicators, detect_patterns
from storage import save_scan, latest_scan, scan_history, stock_history

IST=ZoneInfo("Asia/Kolkata")
def fetch_stock_data(symbol, interval="5m"):
    period="5d" if interval in ("1m","2m","5m","15m","30m") else "1y"
    ticker=symbol if symbol.endswith(".NS") else symbol+".NS"
    df=yf.download(ticker,period=period,interval=interval,auto_adjust=True,progress=False,threads=False)
    if df is None or df.empty: return pd.DataFrame()
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df=df.loc[:,~df.columns.duplicated()].dropna(subset=["Open","High","Low","Close"])
    return df
def scan_nifty50(interval="5m",progress_callback=None):
    symbols=get_nifty50_symbols()
    if not symbols: return pd.DataFrame()
    scan_time=datetime.now(IST).isoformat(timespec="seconds")
    records=[]
    for i,symbol in enumerate(symbols,1):
        try:
            df=fetch_stock_data(symbol,interval)
            if df.empty or len(df)<30: raise ValueError("Insufficient or unavailable price candles")
            x=enrich_indicators(df); r=x.iloc[-1]
            bull=0; bear=0
            if r.Close>r.EMA9>r.EMA21: bull+=25
            if r.Close>r.EMA50: bull+=15
            if r.RSI14>55: bull+=20
            if r.MACD>r.MACD_Signal: bull+=20
            if r.VolumeRatio>1.2: bull+=10
            if r.Close>r.EMA200: bull+=10
            if r.Close<r.EMA9<r.EMA21: bear+=25
            if r.Close<r.EMA50: bear+=15
            if r.RSI14<45: bear+=20
            if r.MACD<r.MACD_Signal: bear+=20
            if r.VolumeRatio>1.2: bear+=10
            if r.Close<r.EMA200: bear+=10
            signal="BULLISH" if bull>=60 and bull>bear else "BEARISH" if bear>=60 and bear>bull else "WAIT / NO TRADE"
            pattern=", ".join(detect_patterns(x))
            records.append((scan_time,symbol,interval,float(r.Close),bull,bear,signal,float(r.RSI14),float(r.MACD),pattern,str(x.index[-1]),"SUCCESS",""))
        except Exception as e:
            records.append((scan_time,symbol,interval,None,0,0,"WAIT / DATA UNAVAILABLE",None,None,"", "", "FAILED",str(e)[:250]))
        if progress_callback: progress_callback(i,len(symbols),symbol)
        time.sleep(0.8)  # sequential; moderate request pacing
    save_scan(records)
    return latest_scan()
def get_latest_scan(): return latest_scan()
def get_scan_history(limit=100): return scan_history(limit)
def get_stock_history(symbol,interval="5m"):
    try: return fetch_stock_data(symbol,interval)
    except Exception: return pd.DataFrame()
