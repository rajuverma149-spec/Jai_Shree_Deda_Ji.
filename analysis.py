import pandas as pd
import numpy as np

def enrich_indicators(df):
    x=df.copy()
    for p in (9,21,50,200): x[f"EMA{p}"]=x.Close.ewm(span=p,adjust=False).mean()
    delta=x.Close.diff()
    gain=delta.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean()
    rs=gain/loss.replace(0,np.nan)
    x["RSI14"]=100-(100/(1+rs))
    e12=x.Close.ewm(span=12,adjust=False).mean(); e26=x.Close.ewm(span=26,adjust=False).mean()
    x["MACD"]=e12-e26; x["MACD_Signal"]=x.MACD.ewm(span=9,adjust=False).mean()
    x["MACD_Hist"]=x.MACD-x.MACD_Signal
    x["SMA20"]=x.Close.rolling(20).mean()
    x["BB_Upper"]=x.SMA20+2*x.Close.rolling(20).std()
    x["BB_Lower"]=x.SMA20-2*x.Close.rolling(20).std()
    tr=pd.concat([x.High-x.Low,(x.High-x.Close.shift()).abs(),(x.Low-x.Close.shift()).abs()],axis=1).max(axis=1)
    x["ATR14"]=tr.rolling(14).mean()
    x["AvgVolume20"]=x.Volume.rolling(20).mean()
    x["VolumeRatio"]=x.Volume/x.AvgVolume20.replace(0,np.nan)
    return x

def detect_patterns(df):
    if df is None or len(df)<2: return ["Insufficient candles"]
    r=df.iloc[-1]; prev=df.iloc[-2]
    body=abs(r.Close-r.Open); rng=max(r.High-r.Low,1e-9)
    upper=r.High-max(r.Open,r.Close); lower=min(r.Open,r.Close)-r.Low
    out=[]
    if body/rng<0.1: out.append("Doji")
    if lower>2*body and upper<body: out.append("Hammer-like")
    if upper>2*body and lower<body: out.append("Shooting-star-like")
    if r.Close>r.Open and prev.Close<prev.Open and r.Close>=prev.Open and r.Open<=prev.Close: out.append("Bullish Engulfing")
    if r.Close<r.Open and prev.Close>prev.Open and r.Open>=prev.Close and r.Close<=prev.Open: out.append("Bearish Engulfing")
    if not out: out.append("No major basic candle pattern detected")
    return out

def candle_pattern_summary(df):
    return {"Latest candle":str(df.index[-1]),"Detected pattern(s)":", ".join(detect_patterns(df))}

def indicator_summary(df):
    r=df.iloc[-1]
    rows=[("Close",r.Close),("RSI (14)",r.RSI14),("MACD",r.MACD),("MACD Signal",r.MACD_Signal),("EMA 9",r.EMA9),("EMA 21",r.EMA21),("EMA 50",r.EMA50),("ATR (14)",r.ATR14),("Volume / 20 avg",r.VolumeRatio)]
    return pd.DataFrame(rows,columns=["Indicator","Latest value"])
