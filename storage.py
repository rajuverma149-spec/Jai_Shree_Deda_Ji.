import sqlite3
import pandas as pd
from pathlib import Path
DB_PATH=Path("mip_data.sqlite3")
def conn(): return sqlite3.connect(DB_PATH,timeout=30)
def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS scans (
        scan_time TEXT, symbol TEXT, interval TEXT, price REAL,
        bullish_score REAL, bearish_score REAL, signal TEXT,
        rsi REAL, macd REAL, candle_pattern TEXT, last_candle TEXT,
        data_status TEXT, error TEXT)""")
def save_scan(rows):
    if not rows: return
    with conn() as c:
        c.executemany("""INSERT INTO scans VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",rows)
def latest_scan():
    with conn() as c:
        return pd.read_sql_query("""SELECT
        scan_time AS "Scan Time", symbol AS "Symbol", interval AS "Timeframe",
        price AS "Price", bullish_score AS "Bullish Score",
        bearish_score AS "Bearish Score", signal AS "Signal",
        rsi AS "RSI", macd AS "MACD", candle_pattern AS "Candle Pattern",
        last_candle AS "Last Candle", data_status AS "Data Status", error AS "Error"
        FROM scans WHERE scan_time=(SELECT MAX(scan_time) FROM scans)""",c)
def scan_history(limit=100):
    with conn() as c:
        return pd.read_sql_query(f"SELECT * FROM scans ORDER BY scan_time DESC LIMIT {int(limit)}",c)
def stock_history(symbol,limit=500):
    with conn() as c:
        return pd.read_sql_query("SELECT * FROM scans WHERE symbol=? ORDER BY scan_time DESC LIMIT ?",c,params=(symbol,int(limit)))
