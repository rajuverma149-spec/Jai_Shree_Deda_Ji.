# Market Intelligence Pro — rebuilt starter

## Features
- Nifty 50 constituents from official Nifty Indices CSV, with a fallback list if the CSV is blocked.
- Sequential scan of all available Nifty 50 symbols.
- Technical score: EMA 9/21/50/200, RSI(14), MACD, volume ratio.
- Top bullish / bearish lists and WAIT / NO TRADE for mixed signals.
- Separate chart, candle-pattern, and RSI/indicator menus.
- SQLite scan history stored in `mip_data.sqlite3`.
- Manual scan plus market-hours polling while the app is awake.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Render
Use:
- Build: `pip install -r requirements.txt`
- Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

SQLite data on a free ephemeral web instance may be lost on redeploy/restart. Persistent storage requires a Render disk or external database. Render Free can sleep; therefore the in-app auto scan cannot guarantee a scan exactly at 09:15 unless the service is kept awake or an external scheduler is configured.

## Data caveats
Yahoo Finance is an unofficial source and can delay, omit, or rate-limit data. Intraday historical availability varies. This app does not promise exchange-grade live data. Pattern detection is intentionally basic; verify before trading.
