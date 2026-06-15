import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import re

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Base */
    .stApp { background-color: #080818; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1rem; max-width: 1400px; }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #1a0533 0%, #0d1b4b 50%, #0a2240 100%);
        border: 1px solid rgba(124, 58, 237, 0.3);
        border-radius: 16px;
        padding: 22px 28px;
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%; right: -10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 70%);
        border-radius: 50%;
    }

    /* Glass cards */
    .glass-card {
        background: rgba(19, 19, 31, 0.85);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 14px 18px;
        transition: border-color 0.2s;
    }
    [data-testid="stMetric"]:hover { border-color: rgba(124,58,237,0.4); }
    [data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 10px !important; text-transform: uppercase; letter-spacing: 0.07em; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 19px !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"]  { font-size: 12px !important; }

    /* Color helpers */
    .pos { color: #22c55e; font-weight: 600; }
    .neg { color: #ef4444; font-weight: 600; }
    .neu { color: #9ca3af; }

    /* Coin badge */
    .coin-badge {
        background: linear-gradient(135deg, #2d1b69, #1e1e2e);
        border: 1px solid rgba(124,58,237,0.3);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 10px;
        color: #a78bfa;
        font-weight: 700;
        text-transform: uppercase;
        display: inline-block;
        letter-spacing: 0.05em;
    }

    /* Section headers */
    h2, h3 { color: #ffffff !important; }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background: #0f0f1a;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #6b7280;
        font-weight: 600;
        font-size: 13px;
        padding: 8px 16px;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7c3aed, #5b21b6) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 10px rgba(124,58,237,0.4);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #5b21b6);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(124,58,237,0.45);
        border: none;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.06) !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0f0f1a; }
    ::-webkit-scrollbar-thumb { background: #2d2d44; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

COINGECKO = "https://api.coingecko.com/api/v3"


# ── Data fetching ─────────────────────────────────────────────────────────────
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
            "rank":       c.get("market_cap_rank"),
            "id":         c.get("id"),
            "name":       c.get("name"),
            "symbol":     c.get("symbol", "").upper(),
            "image":      c.get("image"),
            "price":      c.get("current_price"),
            "pct_1h":     c.get("price_change_percentage_1h_in_currency"),
            "pct_24h":    c.get("price_change_percentage_24h"),
            "pct_7d":     c.get("price_change_percentage_7d_in_currency"),
            "market_cap": c.get("market_cap"),
            "volume_24h": c.get("total_volume"),
            "ath":        c.get("ath"),
            "ath_change": c.get("ath_change_percentage"),
            "sparkline":  c.get("sparkline_in_7d", {}).get("price", []),
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


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fear_greed() -> dict:
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8)
        resp.raise_for_status()
        return resp.json()["data"][0]
    except Exception:
        return None


# ── Formatting helpers ─────────────────────────────────────────────────────────
def fmt_price(val):
    if val is None:   return "—"
    if val < 0.0001:  return f"${val:.8f}"
    if val < 0.01:    return f"${val:.6f}"
    if val < 1:       return f"${val:.4f}"
    return f"${val:,.2f}"

def fmt_large(val):
    if val is None: return "—"
    if val >= 1e12: return f"${val/1e12:.2f}T"
    if val >= 1e9:  return f"${val/1e9:.2f}B"
    if val >= 1e6:  return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"

def pct_color(val):
    if val is None: return "—"
    cls  = "pos" if val > 0 else "neg" if val < 0 else "neu"
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.2f}%</span>'

def fg_label(value: int):
    if value <= 24: return "Extreme Fear", "#ef4444"
    if value <= 44: return "Fear",          "#f97316"
    if value <= 54: return "Neutral",       "#eab308"
    if value <= 74: return "Greed",         "#84cc16"
    return               "Extreme Greed",   "#22c55e"


# ── Onboarding tour ────────────────────────────────────────────────────────────
TOUR_STEPS = [
    ("🔭 Welcome to Crypto Screener!",
     "This dashboard gives you live crypto data in one place — no sign-up or API key needed. Let's walk through what you can do here."),
    ("📊 Market Tab",
     "Browse the top 25–100 coins by market cap. Search by name or ticker, sort any column, and see 1h / 24h / 7d price changes at a glance. A treemap below the table shows coin sizes visually."),
    ("🔥 Trending Tab",
     "See what the crypto community is searching for most right now. High search volume often signals upcoming price moves — keep an eye on these."),
    ("⚡ Top Movers Tab",
     "Spot the biggest gainers and losers in the last 24 hours, plus a 7-day performance bar chart and a market dominance pie chart."),
    ("🔍 Coin Detail Tab",
     "Pick any coin for a deep-dive: candlestick price chart (7–90 days), a 7-day trend line, key stats, and quick momentum signals."),
    ("🌡️ Fear & Greed Index",
     "A sentiment score from 0 (Extreme Fear) to 100 (Extreme Greed). A classic strategy: consider buying during fear, be cautious during greed. You'll find it in the header."),
]

@st.dialog("👋 Quick Tour")
def show_tour_dialog():
    step  = st.session_state.get("tour_step", 0)
    title, body = TOUR_STEPS[step]

    dots = "".join(
        f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin:0 3px;'
        f'background:{"#7c3aed" if i == step else "#2d2d44"};"></span>'
        for i in range(len(TOUR_STEPS))
    )
    st.markdown(f'<div style="text-align:center;margin-bottom:14px;">{dots}</div>', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    st.markdown(
        f'<div class="glass-card" style="color:#c4b5fd;font-size:14px;line-height:1.7;">{body}</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if step > 0 and st.button("← Back", use_container_width=True):
            st.session_state.tour_step = step - 1
            st.rerun()
    with col2:
        st.markdown(
            f'<p style="text-align:center;color:#6b7280;font-size:12px;margin-top:8px;">{step+1} of {len(TOUR_STEPS)}</p>',
            unsafe_allow_html=True,
        )
    with col3:
        if step < len(TOUR_STEPS) - 1:
            if st.button("Next →", use_container_width=True):
                st.session_state.tour_step = step + 1
                st.rerun()
        else:
            if st.button("✓ Done!", use_container_width=True):
                st.session_state.show_tour = False
                st.rerun()

if "show_tour" not in st.session_state:
    st.session_state.show_tour  = True
    st.session_state.tour_step  = 0

if st.session_state.get("show_tour"):
    show_tour_dialog()


# ── Header ─────────────────────────────────────────────────────────────────────
fg_data = fetch_fear_greed()

col_title, col_fg, col_actions = st.columns([4, 2, 1])

with col_title:
    st.markdown("""
<div class="hero-header">
  <div style="font-size:26px;font-weight:800;color:#fff;letter-spacing:-0.5px;">🔭 Crypto Screener</div>
  <div style="color:#a78bfa;font-size:13px;margin-top:5px;">
    Live data via CoinGecko &nbsp;·&nbsp; No API key required &nbsp;·&nbsp; Auto-refreshes every 60s
  </div>
</div>
""", unsafe_allow_html=True)

with col_fg:
    if fg_data:
        fg_val = int(fg_data["value"])
        fg_lbl, fg_clr = fg_label(fg_val)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=fg_val,
            number={"font": {"color": fg_clr, "size": 26, "family": "Inter"}, "suffix": ""},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": "#6b7280",
                    "tickfont": {"size": 9, "color": "#6b7280"},
                    "tickvals": [0, 25, 50, 75, 100],
                },
                "bar": {"color": fg_clr, "thickness": 0.22},
                "bgcolor": "#0f0f1a",
                "bordercolor": "#1e1e2e",
                "steps": [
                    {"range": [0,  25],  "color": "rgba(239,68,68,0.15)"},
                    {"range": [25, 45],  "color": "rgba(249,115,22,0.12)"},
                    {"range": [45, 55],  "color": "rgba(234,179,8,0.12)"},
                    {"range": [55, 75],  "color": "rgba(132,204,22,0.12)"},
                    {"range": [75, 100], "color": "rgba(34,197,94,0.15)"},
                ],
                "threshold": {"line": {"color": fg_clr, "width": 2}, "thickness": 0.75, "value": fg_val},
            },
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=16, b=0),
            height=118,
            annotations=[{
                "text": fg_lbl,
                "x": 0.5, "y": -0.12,
                "xref": "paper", "yref": "paper",
                "showarrow": False,
                "font": {"color": fg_clr, "size": 13, "family": "Inter"},
            }],
        )
        st.markdown(
            '<div style="background:rgba(19,19,31,0.85);border:1px solid rgba(255,255,255,0.06);'
            'border-radius:12px;padding:4px 8px 0;">',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="color:#6b7280;font-size:10px;text-align:center;text-transform:uppercase;'
            'letter-spacing:0.08em;padding-top:6px;">🌡️ Fear &amp; Greed Index</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

with col_actions:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("❓ Tour", use_container_width=True):
        st.session_state.show_tour = True
        st.session_state.tour_step = 0
        st.rerun()


# ── Global market stats ────────────────────────────────────────────────────────
try:
    gdata   = fetch_global()
    mcap    = gdata.get("total_market_cap", {}).get("usd")
    vol     = gdata.get("total_volume", {}).get("usd")
    dom_btc = gdata.get("market_cap_percentage", {}).get("btc")
    dom_eth = gdata.get("market_cap_percentage", {}).get("eth")
    mcap_pct = gdata.get("market_cap_change_percentage_24h_usd")
    active  = gdata.get("active_cryptocurrencies")

    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Total Market Cap", fmt_large(mcap), f"{mcap_pct:+.2f}%" if mcap_pct else None)
    g2.metric("24h Volume",       fmt_large(vol))
    g3.metric("BTC Dominance",    f"{dom_btc:.1f}%" if dom_btc else "—")
    g4.metric("ETH Dominance",    f"{dom_eth:.1f}%" if dom_eth else "—")
    g5.metric("Active Coins",     f"{active:,}"      if active  else "—")
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
    row1, row2 = st.columns([1, 5])
    with row1:
        with st.popover("ℹ️ Guide"):
            st.markdown("""
**Market Table**
- **#** — Market cap rank (1 = largest)
- **Price** — Current USD price
- **1h / 24h / 7d %** — Price change over each window
- **Mkt Cap** — Total value of all coins in circulation
- **Vol 24h** — Trading volume in the last 24 hours
- **ATH Δ** — % below all-time high (0% = at ATH)

💡 *Sort by 24h % for momentum. Sort by ATH Δ for recovery plays.*
""")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        search = st.text_input("", placeholder="🔍  Search by name or ticker…", label_visibility="collapsed")
    with c2:
        per_page = st.selectbox("Show", [25, 50, 100], label_visibility="collapsed")
    with c3:
        sort_col = st.selectbox(
            "Sort by",
            ["rank", "price", "pct_1h", "pct_24h", "pct_7d", "market_cap", "volume_24h"],
            label_visibility="collapsed",
        )

    try:
        with st.spinner("Loading market data…"):
            df = fetch_market(per_page)

        if search:
            mask = (
                df["name"].str.lower().str.contains(search.lower()) |
                df["symbol"].str.lower().str.contains(search.lower())
            )
            df = df[mask]

        df = df.sort_values(sort_col, ascending=(sort_col == "rank"), na_position="last")

        display_rows = []
        for _, row in df.iterrows():
            display_rows.append({
                "#":       int(row["rank"]) if pd.notna(row["rank"]) else "—",
                "Name":    f'{row["name"]} ({row["symbol"]})',
                "Price":   fmt_price(row["price"]),
                "1h %":    f'{row["pct_1h"]:+.2f}%'  if pd.notna(row.get("pct_1h"))  else "—",
                "24h %":   f'{row["pct_24h"]:+.2f}%' if pd.notna(row.get("pct_24h")) else "—",
                "7d %":    f'{row["pct_7d"]:+.2f}%'  if pd.notna(row.get("pct_7d"))  else "—",
                "Mkt Cap": fmt_large(row["market_cap"]),
                "Vol 24h": fmt_large(row["volume_24h"]),
                "ATH Δ":   f'{row["ath_change"]:+.1f}%' if pd.notna(row.get("ath_change")) else "—",
            })

        display_df = pd.DataFrame(display_rows)

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
                "props": [("background-color", "#0f0f1a"), ("color", "#6b7280"), ("font-size", "12px"), ("font-weight", "600")],
            }])
        )

        st.dataframe(styled, use_container_width=True, height=500, hide_index=True)
        st.caption(f"Showing {len(df)} coins · Updated {datetime.now().strftime('%H:%M:%S')}")

        # Market cap treemap
        st.markdown("<br>", unsafe_allow_html=True)
        th1, th2 = st.columns([1, 5])
        with th1:
            with st.popover("ℹ️ What is this?"):
                st.markdown("""
**Market Cap Map**

Each box = one coin. **Size** = market cap (bigger box = more valuable coin). **Color** = 7-day performance.

- 🟢 Green → price rose over 7 days
- 🔴 Red → price fell over 7 days

*Use this to instantly see which large-cap coins are leading or lagging the market.*
""")
        with th2:
            st.markdown("#### 🗺️ Market Cap Map — 7-Day Performance")

        df_tree = df.dropna(subset=["market_cap", "pct_7d"]).head(40)
        fig_tree = px.treemap(
            df_tree,
            path=["symbol"],
            values="market_cap",
            color="pct_7d",
            color_continuous_scale=["#ef4444", "#1e1e2e", "#22c55e"],
            color_continuous_midpoint=0,
            custom_data=["name", "price", "pct_7d", "pct_24h"],
        )
        fig_tree.update_traces(
            texttemplate="<b>%{label}</b><br>%{customdata[2]:.1f}%",
            textfont=dict(size=12, family="Inter"),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Price: %{customdata[1]:$,.4f}<br>"
                "7d: %{customdata[2]:+.2f}%<br>"
                "24h: %{customdata[3]:+.2f}%<extra></extra>"
            ),
        )
        fig_tree.update_layout(
            paper_bgcolor="#0f0f1a",
            margin=dict(l=0, r=0, t=0, b=0),
            height=340,
            coloraxis_colorbar=dict(
                title=dict(text="7d %", font=dict(color="#6b7280", size=11)),
                tickfont=dict(color="#6b7280", size=10),
            ),
        )
        st.plotly_chart(fig_tree, use_container_width=True, config={"displayModeBar": False})

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
    th1, th2 = st.columns([1, 5])
    with th1:
        with st.popover("ℹ️ Why it matters"):
            st.markdown("""
**Search volume = attention**

When lots of people search for a coin, it often signals:
- A news event or viral moment
- Early-stage interest before a price move
- Community excitement

⚠️ *High search volume alone isn't a buy signal — always check the fundamentals too.*
""")
    with th2:
        st.markdown("**Top 15 most searched coins on CoinGecko in the last 24 hours**")

    try:
        with st.spinner("Loading trending…"):
            trending = fetch_trending()

        cols = st.columns(3)
        for i, entry in enumerate(trending):
            item = entry.get("item", {})
            col  = cols[i % 3]
            pct  = item.get("data", {}).get("price_change_percentage_24h", {}).get("usd")
            pct_str       = f"{pct:+.2f}%" if pct is not None else "—"
            pct_color_str = "#22c55e" if (pct or 0) >= 0 else "#ef4444"

            col.markdown(f"""
<div style="background:linear-gradient(135deg,#13131f,#1a1a2e);border:1px solid rgba(255,255,255,0.06);
border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;align-items:center;gap:12px;">
  <span style="color:#4b5563;font-size:13px;font-weight:700;min-width:22px;">#{i+1}</span>
  <img src="{item.get('thumb','')}" width="36" height="36"
       style="border-radius:50%;border:2px solid rgba(124,58,237,0.3);">
  <div style="flex:1;">
    <div style="font-weight:700;color:#fff;font-size:14px;">{item.get('name','')}</div>
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
    th1, th2 = st.columns([1, 5])
    with th1:
        with st.popover("ℹ️ Reading this"):
            st.markdown("""
**Top Gainers & Losers (24h)**

Shows the 10 biggest movers among the top 100 coins by market cap.

- Large single-day moves often partially reverse — watch for overextension
- A coin in both the 24h *and* 7d top gainers has stronger momentum
- A big drop may be a buying opportunity *or* a warning — research why before acting

**Dominance Pie**: shows how much of the total market each major coin controls.
- Rising BTC dominance → capital flowing to safety
- Falling BTC dominance → altcoins gaining (potential "altseason")
""")
    with th2:
        st.markdown("**Biggest movers among the top 100 coins by market cap**")

    try:
        with st.spinner("Loading movers…"):
            df_m = fetch_market(100)

        df_valid = df_m.dropna(subset=["pct_24h"])
        gainers  = df_valid.nlargest(10,  "pct_24h")
        losers   = df_valid.nsmallest(10, "pct_24h")

        col_g, col_l = st.columns(2)

        for col, frame, label, clr in [
            (col_g, gainers, "🚀 Top Gainers (24h)", "#22c55e"),
            (col_l, losers,  "📉 Top Losers (24h)",  "#ef4444"),
        ]:
            with col:
                st.markdown(f"**{label}**")
                for _, row in frame.iterrows():
                    pct       = row["pct_24h"]
                    bar_width = min(abs(pct) * 2, 100)
                    col.markdown(f"""
<div style="background:linear-gradient(135deg,#13131f,#1a1a2e);border:1px solid rgba(255,255,255,0.06);
border-radius:10px;padding:12px 14px;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
    <img src="{row['image']}" width="28" height="28" style="border-radius:50%;">
    <div style="flex:1;">
      <div style="font-weight:600;color:#fff;font-size:13px;">{row['name']}</div>
      <div style="color:#6b7280;font-size:11px;">{fmt_price(row['price'])}</div>
    </div>
    <span style="color:{clr};font-weight:700;font-size:15px;">{pct:+.2f}%</span>
  </div>
  <div style="background:rgba(255,255,255,0.05);border-radius:4px;height:4px;overflow:hidden;">
    <div style="background:{clr};width:{bar_width}%;height:100%;border-radius:4px;opacity:0.7;"></div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.divider()

        col_bar, col_pie = st.columns([3, 2])

        with col_bar:
            st.markdown("**7-Day Performance — Top 20 by Market Cap**")
            df_chart = df_m.dropna(subset=["pct_7d"]).head(20).sort_values("pct_7d")
            colors_bar = ["#22c55e" if v >= 0 else "#ef4444" for v in df_chart["pct_7d"]]
            fig_bar = go.Figure(go.Bar(
                x=df_chart["pct_7d"],
                y=df_chart["symbol"],
                orientation="h",
                marker_color=colors_bar,
                marker_line_width=0,
                text=[f"{v:+.1f}%" for v in df_chart["pct_7d"]],
                textposition="outside",
                textfont=dict(color="#9ca3af", size=10),
            ))
            fig_bar.update_layout(
                paper_bgcolor="#0f0f1a", plot_bgcolor="#13131f",
                font=dict(color="#e2e8f0", size=11, family="Inter"),
                margin=dict(l=10, r=60, t=10, b=10),
                height=430,
                xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#2d2d44", color="#6b7280"),
                yaxis=dict(showgrid=False, color="#e2e8f0"),
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        with col_pie:
            st.markdown("**Market Cap Dominance**")
            try:
                gdata2   = fetch_global()
                dom      = gdata2.get("market_cap_percentage", {})
                top_doms = sorted(dom.items(), key=lambda x: x[1], reverse=True)[:7]
                others   = 100 - sum(v for _, v in top_doms)
                labels   = [k.upper() for k, _ in top_doms] + ["Others"]
                values   = [v for _, v in top_doms] + [others]
                pie_clrs = ["#7c3aed","#3b82f6","#f59e0b","#22c55e","#ef4444","#06b6d4","#a78bfa","#4b5563"]

                fig_pie = go.Figure(go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.55,
                    marker=dict(colors=pie_clrs[:len(labels)], line=dict(color="#0f0f1a", width=2)),
                    textfont=dict(size=11, color="#fff"),
                    hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
                ))
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(font=dict(color="#9ca3af", size=10), bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=430,
                    annotations=[dict(
                        text="Dominance", x=0.5, y=0.5,
                        font=dict(color="#6b7280", size=12, family="Inter"),
                        showarrow=False,
                    )],
                )
                st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
            except Exception:
                st.info("Could not load dominance data.")

    except Exception as e:
        st.error(f"Could not load movers: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 · COIN DETAIL
# ══════════════════════════════════════════════════════════════════════════════
with tab_detail:
    th1, th2 = st.columns([1, 5])
    with th1:
        with st.popover("ℹ️ Reading charts"):
            st.markdown("""
**Candlestick Chart**

Each candle = one time period:
- 🟢 **Green candle** — price went *up* (closed higher than it opened)
- 🔴 **Red candle** — price went *down* (closed lower than it opened)
- **Wick** (thin line) — the high and low for that period

**Key stats:**
- **ATH** = All-Time High (highest price ever recorded)
- **ATL** = All-Time Low (lowest price ever recorded)
- **Circulating Supply** = coins currently in the market
- **Max Supply** = maximum coins that will ever exist (∞ = no hard cap)

**Quick Signals** — simple momentum indicators:
- 🟢 Bullish / positive &nbsp; 🟡 Neutral &nbsp; 🔴 Bearish / negative
""")
    with th2:
        st.markdown("**Deep-dive into any coin**")

    try:
        df_names = fetch_market(100)
        coin_options = {f"{r['name']} ({r['symbol']})": r["id"] for _, r in df_names.iterrows()}

        col_sel, col_range = st.columns([2, 2])
        with col_sel:
            selected_label = st.selectbox("Select a coin", list(coin_options.keys()))
        with col_range:
            ohlc_days = st.radio("Chart range", [7, 14, 30, 90], horizontal=True, index=0)

        selected_id = coin_options[selected_label]

        with st.spinner("Loading coin detail…"):
            detail = fetch_coin_detail(selected_id)
            ohlc   = fetch_ohlc(selected_id, ohlc_days)

        col_info, col_chart = st.columns([1, 2])

        with col_info:
            mdata  = detail.get("market_data", {})
            price  = mdata.get("current_price", {}).get("usd")
            pct24  = mdata.get("price_change_percentage_24h")
            pct7   = mdata.get("price_change_percentage_7d_in_currency", {}).get("usd")
            pct30  = mdata.get("price_change_percentage_30d_in_currency", {}).get("usd")
            mcap_d = mdata.get("market_cap", {}).get("usd")
            vol_d  = mdata.get("total_volume", {}).get("usd")
            ath_d  = mdata.get("ath", {}).get("usd")
            atl_d  = mdata.get("atl", {}).get("usd")
            supply = mdata.get("circulating_supply")
            max_s  = mdata.get("max_supply")

            st.markdown(f"""
<div style="background:linear-gradient(135deg,#13131f,#1a1a2e);border:1px solid rgba(255,255,255,0.06);
border-radius:14px;padding:20px;">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
    <img src="{detail.get('image',{}).get('small','')}" width="44" height="44"
         style="border-radius:50%;border:2px solid rgba(124,58,237,0.4);">
    <div>
      <div style="font-size:20px;font-weight:800;color:#fff;">{detail.get('name','')}</div>
      <span class="coin-badge">{detail.get('symbol','').upper()}</span>
    </div>
  </div>
  <div style="font-size:30px;font-weight:800;color:#fff;letter-spacing:-1px;margin-bottom:2px;">{fmt_price(price)}</div>
  <div style="margin-bottom:16px;font-size:14px;">{pct_color(pct24)}
    <span style="color:#6b7280;font-size:12px;"> 24h change</span></div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">7d change</td>
        <td style="text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{pct_color(pct7)}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">30d change</td>
        <td style="text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{pct_color(pct30)}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">Market Cap</td>
        <td style="color:#e2e8f0;text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{fmt_large(mcap_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">Volume 24h</td>
        <td style="color:#e2e8f0;text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{fmt_large(vol_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">All-Time High</td>
        <td style="color:#e2e8f0;text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{fmt_price(ath_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">All-Time Low</td>
        <td style="color:#e2e8f0;text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{fmt_price(atl_d)}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">Circulating Supply</td>
        <td style="color:#e2e8f0;text-align:right;border-bottom:1px solid rgba(255,255,255,0.04);">{f"{supply:,.0f}" if supply else "—"}</td></tr>
    <tr><td style="color:#6b7280;padding:6px 0;">Max Supply</td>
        <td style="color:#e2e8f0;text-align:right;">{f"{max_s:,.0f}" if max_s else "∞"}</td></tr>
  </table>
</div>
""", unsafe_allow_html=True)

            # Quick signals
            signals = []
            if pct24 is not None:
                signals.append(("24h momentum", "🟢" if pct24 > 2 else "🔴" if pct24 < -2 else "🟡", f"{pct24:+.1f}%"))
            if pct7 is not None:
                signals.append(("7d trend",     "🟢" if pct7  > 5 else "🔴" if pct7  < -5 else "🟡", f"{pct7:+.1f}%"))
            if ath_d and price:
                ath_pct = ((price - ath_d) / ath_d) * 100
                signals.append(("Distance from ATH", "🟢" if ath_pct > -20 else "🔴" if ath_pct < -70 else "🟡", f"{ath_pct:+.1f}%"))
            if vol_d and mcap_d and mcap_d > 0:
                vol_ratio = vol_d / mcap_d
                signals.append(("Volume/Mkt Cap", "🟢" if vol_ratio > 0.1 else "🟡" if vol_ratio > 0.05 else "🔴", f"{vol_ratio:.2%}"))

            if signals:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    '<div style="color:#6b7280;font-size:10px;text-transform:uppercase;'
                    'letter-spacing:0.08em;margin-bottom:8px;">Quick Signals</div>',
                    unsafe_allow_html=True,
                )
                for lbl, icon, val in signals:
                    st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
background:rgba(19,19,31,0.85);border:1px solid rgba(255,255,255,0.06);
border-radius:8px;padding:8px 12px;margin-bottom:6px;">
  <span style="color:#9ca3af;font-size:12px;">{icon} {lbl}</span>
  <span style="color:#e2e8f0;font-size:12px;font-weight:600;">{val}</span>
</div>
""", unsafe_allow_html=True)
                st.caption("⚠️ Signals are for reference only — not financial advice.")

        with col_chart:
            if not ohlc.empty:
                fig_candle = go.Figure(go.Candlestick(
                    x=ohlc["date"],
                    open=ohlc["open"], high=ohlc["high"],
                    low=ohlc["low"],   close=ohlc["close"],
                    increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
                    increasing_fillcolor="rgba(34,197,94,0.2)", decreasing_fillcolor="rgba(239,68,68,0.2)",
                ))
                fig_candle.update_layout(
                    title=dict(
                        text=f"{detail.get('name','')} — {ohlc_days}d Price Chart",
                        font=dict(color="#e2e8f0", size=14, family="Inter"),
                    ),
                    paper_bgcolor="#0f0f1a", plot_bgcolor="#13131f",
                    font=dict(color="#e2e8f0", family="Inter"),
                    xaxis=dict(showgrid=False, color="#6b7280", rangeslider_visible=False),
                    yaxis=dict(showgrid=True, gridcolor="#1e1e2e", color="#6b7280"),
                    margin=dict(l=10, r=10, t=40, b=10),
                    height=400,
                )
                st.plotly_chart(fig_candle, use_container_width=True, config={"displayModeBar": False})

            # 7-day sparkline
            sp_row = df_names[df_names["id"] == selected_id]["sparkline"].values
            if len(sp_row) > 0 and sp_row[0]:
                prices    = sp_row[0]
                sp_color      = "rgba(34,197,94," if prices[-1] >= prices[0] else "rgba(239,68,68,"
                sp_line_color = "#22c55e"         if prices[-1] >= prices[0] else "#ef4444"
                fig_spark = go.Figure(go.Scatter(
                    y=prices, mode="lines",
                    line=dict(color=sp_line_color, width=2),
                    fill="tozeroy",
                    fillcolor=sp_color + "0.12)",
                ))
                fig_spark.update_layout(
                    title=dict(text="7-Day Price Trend", font=dict(color="#6b7280", size=12)),
                    paper_bgcolor="#0f0f1a", plot_bgcolor="#13131f",
                    margin=dict(l=10, r=10, t=28, b=10),
                    height=130,
                    xaxis=dict(visible=False),
                    yaxis=dict(showgrid=True, gridcolor="#1e1e2e", color="#6b7280", tickfont=dict(size=9)),
                    showlegend=False,
                )
                st.plotly_chart(fig_spark, use_container_width=True, config={"displayModeBar": False})

        # Description
        desc = detail.get("description", {}).get("en", "")
        if desc:
            with st.expander("📖 About this coin"):
                clean = re.sub(r"<[^>]+>", "", desc)
                st.markdown(clean[:1500] + ("…" if len(clean) > 1500 else ""))

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.warning("⚠️ CoinGecko rate limit hit. Wait ~60 seconds and click Refresh.")
        else:
            st.error(f"Could not load coin detail: {e}")
    except Exception as e:
        st.error(f"Could not load coin detail: {e}")
