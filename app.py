import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Screener",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp { background-color: #0f0f1a; }
    .block-container { padding-top: 1.5rem; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #13131f;
        border: 1px solid #1e1e2e;
        border-radius: 10px;
        padding: 14px 18px;
    }
    [data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 12px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 22px !important; }

    /* Positive / negative color helpers */
    .pos { color: #22c55e; font-weight: 600; }
    .neg { color: #ef4444; font-weight: 600; }
    .neu { color: #9ca3af; }

    /* Coin badge */
    .coin-badge {
        background: #1e1e2e;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
        color: #a78bfa;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
    }

    /* Section headers */
    h2, h3 { color: #ffffff !important; }

    /* Hide default Streamlit branding */
    #MainMenu, footer { visibility: hidden; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #1e1e2e;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
        padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] {
        background: #7c3aed !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

COINGECKO = "https://api.coingecko.com/api/v3"


# ── Data fetching with caching ─────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch_market(per_page: int = 50) -> pd.DataFrame:
    url = (
        f"{COINGECKO}/coins/markets"
        f"?vs_currency=usd&order=market_cap_desc"
        f"&per_page={per_page}&page=1"
        f"&sparkline=true"
        f"&price_change_percentage=1h,24h,7d"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for c in data:
        rows.append({
            "rank":        c.get("market_cap_rank"),
            "id":          c.get("id"),
            "name":        c.get("name"),
            "symbol":      c.get("symbol", "").upper(),
            "image":       c.get("image"),
            "price":       c.get("current_price"),
            "pct_1h":      c.get("price_change_percentage_1h_in_currency"),
            "pct_24h":     c.get("price_change_percentage_24h"),
            "pct_7d":      c.get("price_change_percentage_7d_in_currency"),
            "market_cap":  c.get("market_cap"),
            "volume_24h":  c.get("total_volume"),
            "ath":         c.get("ath"),
            "ath_change":  c.get("ath_change_percentage"),
            "sparkline":   c.get("sparkline_in_7d", {}).get("price", []),
            "last_updated": c.get("last_updated"),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=120, show_spinner=False)
def fetch_trending() -> list:
    resp = requests.get(f"{COINGECKO}/search/trending", timeout=15)
    resp.raise_for_status()
    return resp.json().get("coins", [])


@st.cache_data(ttl=300, show_spinner=False)
def fetch_global() -> dict:
    resp = requests.get(f"{COINGECKO}/global", timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {})


@st.cache_data(ttl=60, show_spinner=False)
def fetch_coin_detail(coin_id: str) -> dict:
    resp = requests.get(
        f"{COINGECKO}/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false",
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlc(coin_id: str, days: int = 7) -> pd.DataFrame:
    resp = requests.get(
        f"{COINGECKO}/coins/{coin_id}/ohlc?vs_currency=usd&days={days}",
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


# ── Formatting helpers ─────────────────────────────────────────────────────────
def fmt_price(val):
    if val is None:
        return "—"
    if val < 0.0001:
        return f"${val:.8f}"
    if val < 0.01:
        return f"${val:.6f}"
    if val < 1:
        return f"${val:.4f}"
    return f"${val:,.2f}"


def fmt_large(val):
    if val is None:
        return "—"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    if val >= 1e6:
        return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"


def pct_color(val):
    if val is None:
        return "—"
    cls = "pos" if val > 0 else "neg" if val < 0 else "neu"
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.2f}%</span>'


def sparkline_fig(prices: list, color: str = "#7c3aed"):
    if not prices or len(prices) < 2:
        return None
    fig = go.Figure(go.Scatter(
        y=prices, mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=color.replace(")", ", 0.08)").replace("rgb", "rgba") if "rgb" in color else color + "14",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=40, width=90,
        showlegend=False,
    )
    return fig


# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_refresh = st.columns([5, 1])
with col_title:
    st.markdown("## 🔭 Crypto Screener")
    st.markdown('<p style="color:#6b7280;font-size:13px;margin-top:-12px;">Live data via CoinGecko · Free tier · Auto-refreshes every 60s</p>', unsafe_allow_html=True)
with col_refresh:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Global market stats ────────────────────────────────────────────────────────
try:
    gdata = fetch_global()
    mcap   = gdata.get("total_market_cap", {}).get("usd")
    vol    = gdata.get("total_volume", {}).get("usd")
    dom_btc = gdata.get("market_cap_percentage", {}).get("btc")
    dom_eth = gdata.get("market_cap_percentage", {}).get("eth")
    mcap_pct = gdata.get("market_cap_change_percentage_24h_usd")

    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Total Market Cap", fmt_large(mcap), f"{mcap_pct:+.2f}%" if mcap_pct else None)
    g2.metric("24h Volume",       fmt_large(vol))
    g3.metric("BTC Dominance",    f"{dom_btc:.1f}%" if dom_btc else "—")
    g4.metric("ETH Dominance",    f"{dom_eth:.1f}%" if dom_eth else "—")
    g5.metric("Active Coins",     f"{gdata.get('active_cryptocurrencies', '—'):,}" if gdata.get('active_cryptocurrencies') else "—")
except Exception as e:
    st.warning(f"Could not load global stats: {e}")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_market, tab_trending, tab_movers, tab_detail = st.tabs([
    "📊 Market", "🔥 Trending", "⚡ Top Movers", "🔍 Coin Detail"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · MARKET
# ══════════════════════════════════════════════════════════════════════════════
with tab_market:
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        search = st.text_input("", placeholder="🔍  Search by name or ticker…", label_visibility="collapsed")
    with c2:
        per_page = st.selectbox("Show", [25, 50, 100], label_visibility="collapsed")
    with c3:
        sort_col = st.selectbox("Sort by", ["rank", "price", "pct_1h", "pct_24h", "pct_7d", "market_cap", "volume_24h"], label_visibility="collapsed")

    try:
        with st.spinner("Loading market data…"):
            df = fetch_market(per_page)

        if search:
            mask = (
                df["name"].str.lower().str.contains(search.lower()) |
                df["symbol"].str.lower().str.contains(search.lower())
            )
            df = df[mask]

        ascending = sort_col == "rank"
        df = df.sort_values(sort_col, ascending=ascending, na_position="last")

        # Build display table
        display_rows = []
        for _, row in df.iterrows():
            sp_color = "#22c55e" if (row["pct_7d"] or 0) >= 0 else "#ef4444"
            display_rows.append({
                "#":        int(row["rank"]) if pd.notna(row["rank"]) else "—",
                "Name":     f'{row["name"]} ({row["symbol"]})',
                "Price":    fmt_price(row["price"]),
                "1h %":     f'{row["pct_1h"]:+.2f}%' if pd.notna(row.get("pct_1h")) else "—",
                "24h %":    f'{row["pct_24h"]:+.2f}%' if pd.notna(row.get("pct_24h")) else "—",
                "7d %":     f'{row["pct_7d"]:+.2f}%' if pd.notna(row.get("pct_7d")) else "—",
                "Mkt Cap":  fmt_large(row["market_cap"]),
                "Vol 24h":  fmt_large(row["volume_24h"]),
                "ATH Δ":    f'{row["ath_change"]:+.1f}%' if pd.notna(row.get("ath_change")) else "—",
            })

        display_df = pd.DataFrame(display_rows)

        # Color pct columns
        def color_pct(val):
            if isinstance(val, str) and val.startswith("+"):
                return "color: #22c55e; font-weight: 600"
            if isinstance(val, str) and val.startswith("-"):
                return "color: #ef4444; font-weight: 600"
            return "color: #9ca3af"

        styled = (
            display_df.style
            .map(color_pct, subset=["1h %", "24h %", "7d %", "ATH Δ"])
            .set_properties(**{"background-color": "#13131f", "color": "#e2e8f0", "border": "1px solid #1e1e2e"})
            .set_table_styles([{
                "selector": "th",
                "props": [("background-color", "#0f0f1a"), ("color", "#6b7280"), ("font-size", "12px"), ("font-weight", "600")]
            }])
        )

        st.dataframe(styled, use_container_width=True, height=600, hide_index=True)
        st.caption(f"Showing {len(df)} coins · Updated {datetime.now().strftime('%H:%M:%S')}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.error("⚠️ CoinGecko rate limit hit. Wait ~60 seconds and click Refresh.")
        else:
            st.error(f"API error: {e}")
    except Exception as e:
        st.error(f"Something went wrong: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · TRENDING
# ══════════════════════════════════════════════════════════════════════════════
with tab_trending:
    st.markdown("**Top 15 most searched coins on CoinGecko in the last 24 hours**")
    try:
        with st.spinner("Loading trending…"):
            trending = fetch_trending()

        cols = st.columns(3)
        for i, entry in enumerate(trending):
            item = entry.get("item", {})
            col = cols[i % 3]
            pct = item.get("data", {}).get("price_change_percentage_24h", {}).get("usd")
            pct_str = f"{pct:+.2f}%" if pct is not None else "—"
            pct_color_str = "#22c55e" if (pct or 0) >= 0 else "#ef4444"

            col.markdown(f"""
<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:12px;">
  <span style="color:#4b5563;font-size:13px;min-width:20px;">#{i+1}</span>
  <img src="{item.get('thumb','')}" width="36" height="36" style="border-radius:50%;">
  <div style="flex:1;">
    <div style="font-weight:600;color:#fff;font-size:14px;">{item.get('name','')}</div>
    <span class="coin-badge">{item.get('symbol','')}</span>
    <span style="color:#6b7280;font-size:11px;margin-left:6px;">Rank #{item.get('market_cap_rank','—')}</span>
  </div>
  <span style="color:{pct_color_str};font-weight:700;font-size:14px;">{pct_str}</span>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Could not load trending: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 · TOP MOVERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_movers:
    try:
        with st.spinner("Loading movers…"):
            df_m = fetch_market(100)

        df_valid = df_m.dropna(subset=["pct_24h"])
        gainers = df_valid.nlargest(10, "pct_24h")
        losers  = df_valid.nsmallest(10, "pct_24h")

        col_g, col_l = st.columns(2)

        for col, frame, label, clr in [
            (col_g, gainers, "🚀 Top Gainers (24h)", "#22c55e"),
            (col_l, losers,  "📉 Top Losers (24h)",  "#ef4444"),
        ]:
            with col:
                st.markdown(f"**{label}**")
                for _, row in frame.iterrows():
                    pct = row["pct_24h"]
                    col.markdown(f"""
<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:10px;padding:12px 14px;margin-bottom:8px;display:flex;align-items:center;gap:10px;">
  <img src="{row['image']}" width="30" height="30" style="border-radius:50%;">
  <div style="flex:1;">
    <div style="font-weight:600;color:#fff;font-size:13px;">{row['name']}</div>
    <div style="color:#6b7280;font-size:11px;">{fmt_price(row['price'])}</div>
  </div>
  <span style="color:{clr};font-weight:700;font-size:14px;">{pct:+.2f}%</span>
</div>
""", unsafe_allow_html=True)

        st.divider()
        st.markdown("**7-Day Performance — Top 20 by Market Cap**")
        df_chart = df_m.dropna(subset=["pct_7d"]).head(20).sort_values("pct_7d")
        colors = ["#22c55e" if v >= 0 else "#ef4444" for v in df_chart["pct_7d"]]
        fig_bar = go.Figure(go.Bar(
            x=df_chart["pct_7d"],
            y=df_chart["symbol"],
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in df_chart["pct_7d"]],
            textposition="outside",
        ))
        fig_bar.update_layout(
            paper_bgcolor="#0f0f1a", plot_bgcolor="#0f0f1a",
            font=dict(color="#e2e8f0", size=12),
            margin=dict(l=10, r=60, t=10, b=10),
            height=500,
            xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#2d2d44", color="#6b7280"),
            yaxis=dict(showgrid=False, color="#e2e8f0"),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load movers: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 · COIN DETAIL
# ══════════════════════════════════════════════════════════════════════════════
with tab_detail:
    try:
        df_names = fetch_market(100)
        coin_options = {f"{r['name']} ({r['symbol']})": r["id"] for _, r in df_names.iterrows()}
        selected_label = st.selectbox("Select a coin", list(coin_options.keys()))
        selected_id    = coin_options[selected_label]
        ohlc_days      = st.radio("Chart range", [7, 14, 30, 90], horizontal=True, index=0)

        col_info, col_chart = st.columns([1, 2])

        with st.spinner("Loading coin detail…"):
            detail = fetch_coin_detail(selected_id)
            ohlc   = fetch_ohlc(selected_id, ohlc_days)

        with col_info:
            mdata = detail.get("market_data", {})
            price   = mdata.get("current_price", {}).get("usd")
            pct24   = mdata.get("price_change_percentage_24h")
            pct7    = mdata.get("price_change_percentage_7d_in_currency", {}).get("usd")
            pct30   = mdata.get("price_change_percentage_30d_in_currency", {}).get("usd")
            mcap_d  = mdata.get("market_cap", {}).get("usd")
            vol_d   = mdata.get("total_volume", {}).get("usd")
            ath_d   = mdata.get("ath", {}).get("usd")
            atl_d   = mdata.get("atl", {}).get("usd")
            supply  = mdata.get("circulating_supply")
            max_s   = mdata.get("max_supply")

            st.markdown(f"""
<div style="background:#13131f;border:1px solid #1e1e2e;border-radius:12px;padding:20px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
    <img src="{detail.get('image',{}).get('small','')}" width="44" height="44" style="border-radius:50%;">
    <div>
      <div style="font-size:20px;font-weight:700;color:#fff;">{detail.get('name','')}</div>
      <span class="coin-badge">{detail.get('symbol','').upper()}</span>
    </div>
  </div>
  <div style="font-size:28px;font-weight:700;color:#fff;margin-bottom:4px;">{fmt_price(price)}</div>
  <div style="margin-bottom:16px;">{pct_color(pct24)} 24h</div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="color:#6b7280;padding:5px 0;">7d change</td><td style="text-align:right;">{pct_color(pct7)}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">30d change</td><td style="text-align:right;">{pct_color(pct30)}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">Market Cap</td><td style="color:#e2e8f0;text-align:right;">{fmt_large(mcap_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">Volume 24h</td><td style="color:#e2e8f0;text-align:right;">{fmt_large(vol_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">All-Time High</td><td style="color:#e2e8f0;text-align:right;">{fmt_price(ath_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">All-Time Low</td><td style="color:#e2e8f0;text-align:right;">{fmt_price(atl_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">Circulating Supply</td><td style="color:#e2e8f0;text-align:right;">{f"{supply:,.0f}" if supply else "—"}</td></tr>
    <tr><td style="color:#6b7280;padding:5px 0;">Max Supply</td><td style="color:#e2e8f0;text-align:right;">{f"{max_s:,.0f}" if max_s else "∞"}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

        with col_chart:
            if not ohlc.empty:
                fig_candle = go.Figure(go.Candlestick(
                    x=ohlc["date"],
                    open=ohlc["open"], high=ohlc["high"],
                    low=ohlc["low"],  close=ohlc["close"],
                    increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
                    increasing_fillcolor="#22c55e", decreasing_fillcolor="#ef4444",
                ))
                fig_candle.update_layout(
                    title=f"{detail.get('name','')} — {ohlc_days}d OHLC",
                    paper_bgcolor="#0f0f1a", plot_bgcolor="#13131f",
                    font=dict(color="#e2e8f0"),
                    xaxis=dict(showgrid=False, color="#6b7280", rangeslider_visible=False),
                    yaxis=dict(showgrid=True, gridcolor="#1e1e2e", color="#6b7280"),
                    margin=dict(l=10, r=10, t=40, b=10),
                    height=400,
                )
                st.plotly_chart(fig_candle, use_container_width=True)

        # Description
        desc = detail.get("description", {}).get("en", "")
        if desc:
            with st.expander("About this coin"):
                # Strip HTML tags simply
                import re
                clean = re.sub(r"<[^>]+>", "", desc)
                st.markdown(clean[:1200] + ("…" if len(clean) > 1200 else ""))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.warning("⚠️ CoinGecko rate limit hit. Wait ~60 seconds and click Refresh.")
        else:
            st.error(f"Could not load coin detail: {e}")
    except Exception as e:
        st.error(f"Could not load coin detail: {e}")
