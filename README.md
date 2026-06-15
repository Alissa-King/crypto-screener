# 🔭 Crypto Screener

A live crypto research dashboard built with Streamlit and the free CoinGecko API.
No API key required.

## Features

- **📊 Market tab** — sortable table with price, 1h/24h/7d % changes, market cap, volume
- **🔥 Trending tab** — top 15 most-searched coins on CoinGecko right now
- **⚡ Top Movers tab** — biggest gainers/losers + 7d performance bar chart
- **🔍 Coin Detail tab** — candlestick OHLC chart, full stats, coin description

---

## Run locally

```bash
# 1. Clone or download this folder
cd crypto_screener_app

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at http://localhost:8501

---

## Deploy to Streamlit Community Cloud (free)

1. Push this folder to a GitHub repo
2. Go to https://share.streamlit.io
3. Click **New app** → connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Deploy** — done! You get a public URL.

## Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

Add a `Procfile` with:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

## Deploy to Render

1. Push to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your repo
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
6. Deploy

---

## Notes

- CoinGecko free tier allows ~30 requests/minute. The app caches data for 60 seconds to stay within limits.
- If you see a 429 error, wait 60 seconds and click **↻ Refresh**.
- For higher rate limits, sign up for a free CoinGecko API key at https://www.coingecko.com/en/api and add it as an environment variable `COINGECKO_API_KEY`.

## Extending this app

Ideas for next steps:
- **Watchlist** — add Supabase to persist a personal watchlist across sessions
- **Alerts** — use `st.experimental_rerun()` on a timer + email/SMS via Twilio when price crosses a threshold
- **Portfolio tracker** — enter your holdings and track P&L live
- **Fear & Greed Index** — free API at https://alternative.me/crypto/fear-and-greed-index/
- **On-chain data** — Glassnode or Dune Analytics APIs for deeper signals
