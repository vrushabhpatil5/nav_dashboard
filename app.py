# app.py
# Live Fund NAV Dashboard — Streamlit Frontend

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import time
from nav_engine import fetch_prices, get_fund_summary
from portfolio import PORTFOLIO, FUND_NAME

REQUIRED_COLUMNS = {"ticker", "name", "shares", "cost_price", "asset_class", "sector"}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NAV Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
  .alert-box {
    background: #2d1a1a; border-left: 4px solid #ff4757;
    padding: 10px 16px; border-radius: 4px; margin-bottom: 8px;
  }
  .ok-box {
    background: #1a2d1e; border-left: 4px solid #00e87a;
    padding: 10px 16px; border-radius: 4px; margin-bottom: 8px;
  }
  .info-box {
    background: #1a1e2d; border-left: 4px solid #4a90e2;
    padding: 10px 16px; border-radius: 4px; margin-bottom: 8px;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title(f"📊 {FUND_NAME}")
st.caption("Live NAV Dashboard · Prices via Yahoo Finance (15-min delay) · For educational purposes only")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Portfolio Source")

    portfolio_mode = st.radio(
        "Choose how to load portfolio:",
        ["Use default portfolio", "Upload CSV file"],
        index=0
    )

    uploaded_file = None
    if portfolio_mode == "Upload CSV file":
        st.markdown("**Required columns:**")
        st.code("ticker, name, shares, cost_price, asset_class, sector")
        uploaded_file = st.file_uploader(
            "Upload portfolio CSV",
            type=["csv"],
            help="Upload a CSV with your portfolio holdings"
        )
        st.markdown(
            '<div class="info-box">💡 Download the sample CSV below to get started.</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.header("⚙️ Controls")
    auto_refresh = st.toggle("Auto-refresh (60s)", value=False)
    refresh_btn = st.button("🔄 Refresh Now", width="stretch")
    st.divider()
    st.subheader("🔍 Filter")
    asset_filter = st.multiselect(
        "Asset Class",
        options=["Equity", "ETF", "Bond ETF"],
        default=["Equity", "ETF", "Bond ETF"]
    )
    st.divider()
    st.caption("Built by Vrushabh · MSc International Accounting & Finance · Dublin Business School")

# ── Sample CSV download ───────────────────────────────────────────────────────
sample_csv = """ticker,name,shares,cost_price,asset_class,sector
NVDA,NVIDIA Corp,150,80.00,Equity,Information Technology
AAPL,Apple Inc,200,150.00,Equity,Information Technology
GOOGL,Alphabet Inc,180,120.00,Equity,Communication Services
MSFT,Microsoft Corp,120,280.00,Equity,Information Technology
AMZN,Amazon.com Inc,130,130.00,Equity,Consumer Discretionary
TSM,Taiwan Semiconductor,200,90.00,Equity,Information Technology
AVGO,Broadcom Inc,80,550.00,Equity,Information Technology
TSLA,Tesla Inc,160,200.00,Equity,Consumer Discretionary
META,Meta Platforms Inc,100,250.00,Equity,Communication Services
ASML,ASML Holding NV,40,600.00,Equity,Information Technology
SPY,SPDR S&P 500 ETF,300,420.00,ETF,US Equity
QQQ,Invesco QQQ Nasdaq 100,150,350.00,ETF,US Tech Equity
IEMG,iShares MSCI Emerging Mkts,400,48.00,ETF,Emerging Markets
AGG,iShares US Aggregate Bond,300,96.00,Bond ETF,Fixed Income
"""

st.download_button(
    label="📥 Download Sample CSV",
    data=sample_csv,
    file_name="sample_portfolio.csv",
    mime="text/csv",
    help="Download a sample portfolio CSV to use as a template"
)

st.divider()

# ── Load portfolio ────────────────────────────────────────────────────────────
def load_portfolio_from_csv(file) -> list[dict] | None:
    """Parse and validate uploaded CSV into portfolio list."""
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip().str.lower()

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            st.error(f"❌ Missing columns in CSV: {', '.join(missing)}")
            return None

        df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
        df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce")

        invalid = df[df["shares"].isna() | df["cost_price"].isna()]
        if not invalid.empty:
            st.warning(f"⚠️ {len(invalid)} row(s) skipped due to invalid shares/cost_price values.")
            df = df.dropna(subset=["shares", "cost_price"])

        if df.empty:
            st.error("❌ No valid rows found in CSV.")
            return None

        return df.to_dict(orient="records")

    except Exception as e:
        st.error(f"❌ Could not read CSV: {e}")
        return None


# Decide which portfolio to use
if portfolio_mode == "Upload CSV file" and uploaded_file:
    portfolio = load_portfolio_from_csv(uploaded_file)
    if portfolio is None:
        st.stop()
    st.markdown(
        f'<div class="ok-box">✅ CSV loaded successfully — <b>{len(portfolio)} holdings</b> found.</div>',
        unsafe_allow_html=True
    )
else:
    portfolio = PORTFOLIO
    if portfolio_mode == "Upload CSV file" and not uploaded_file:
        st.markdown(
            '<div class="info-box">📁 No CSV uploaded yet — showing default portfolio. Upload a CSV in the sidebar to use your own.</div>',
            unsafe_allow_html=True
        )

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data(portfolio_key: str, portfolio_data: list):
    tickers = [h["ticker"] for h in portfolio_data]
    prices = fetch_prices(tickers)
    df = calculate_nav_from_portfolio(prices, portfolio_data)
    summary = get_fund_summary(df)
    return df, summary


def calculate_nav_from_portfolio(price_data: dict, portfolio_data: list) -> pd.DataFrame:
    """Wrapper to calculate NAV from any portfolio list."""
    import numpy as np
    from datetime import datetime

    rows = []
    for holding in portfolio_data:
        ticker = str(holding["ticker"]).strip().upper()
        px = price_data.get(ticker, {})

        current_price = px.get("price")
        prev_close = px.get("prev_close")
        cost_price = float(holding["cost_price"])
        shares = float(holding["shares"])

        market_value = round(current_price * shares, 2) if current_price else None
        cost_basis = round(cost_price * shares, 2)
        unrealised_pnl = round(market_value - cost_basis, 2) if market_value else None
        unrealised_pct = round((unrealised_pnl / cost_basis) * 100, 2) if unrealised_pnl is not None else None
        daily_pnl = round((current_price - prev_close) * shares, 2) if current_price and prev_close else None
        daily_pct = round(((current_price - prev_close) / prev_close) * 100, 2) if current_price and prev_close and prev_close != 0 else None

        rows.append({
            "Ticker":          ticker,
            "Name":            holding.get("name", ticker),
            "Asset Class":     holding.get("asset_class", "—"),
            "Sector":          holding.get("sector", "—"),
            "Shares":          shares,
            "Cost Price":      cost_price,
            "Current Price":   current_price,
            "Cost Basis":      cost_basis,
            "Market Value":    market_value,
            "Unrealised P&L":  unrealised_pnl,
            "Unrealised %":    unrealised_pct,
            "Daily P&L":       daily_pnl,
            "Daily %":         daily_pct,
            "Stale Price":     px.get("stale", False),
            "Missing Price":   px.get("missing", False),
            "Price As At":     px.get("fetched_at", "—"),
        })

    df = pd.DataFrame(rows)
    total_mv = df["Market Value"].sum()
    df["Weight %"] = df["Market Value"].apply(
        lambda mv: round((mv / total_mv) * 100, 2) if total_mv and mv else None
    )
    return df


if refresh_btn:
    st.cache_data.clear()

# Use a cache key based on portfolio content so CSV changes trigger a reload
portfolio_key = str([(h["ticker"], h["shares"], h["cost_price"]) for h in portfolio])
df, summary = load_data(portfolio_key, portfolio)

# Apply filter
df_filtered = df[df["Asset Class"].isin(asset_filter)] if asset_filter else df

# ── NAV Summary Cards ─────────────────────────────────────────────────────────
st.subheader("📌 Fund NAV Summary")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("Total NAV", f"${summary['nav']:,.0f}")
with c2:
    st.metric("Unrealised P&L",
              f"${summary['unrealised_pnl']:,.0f}",
              f"{summary['unrealised_pct']:+.2f}%")
with c3:
    st.metric("Daily P&L", f"${summary['daily_pnl']:,.0f}")
with c4:
    st.metric("Holdings", summary['num_holdings'])
with c5:
    alert_color = "🔴" if summary['pricing_alerts'] > 0 else "🟢"
    st.metric(f"{alert_color} Pricing Alerts", summary['pricing_alerts'])

st.caption(f"Last calculated: {summary['last_calculated']}")
st.divider()

# ── Pricing Alerts ────────────────────────────────────────────────────────────
alerts = df[df["Stale Price"] | df["Missing Price"]]
if not alerts.empty:
    st.subheader("⚠️ Pricing Alerts")
    for _, row in alerts.iterrows():
        reason = "Missing price" if row["Missing Price"] else "Stale price"
        st.markdown(
            f'<div class="alert-box">⚠️ <b>{row["Ticker"]} — {row["Name"]}</b>: {reason} detected. '
            f'Using fallback (prev close). Review before NAV sign-off.</div>',
            unsafe_allow_html=True
        )
    st.divider()
else:
    st.markdown('<div class="ok-box">✅ All prices validated. No anomalies detected.</div>', unsafe_allow_html=True)
    st.divider()

# ── Holdings Table ────────────────────────────────────────────────────────────
st.subheader("📋 Holdings Breakdown")

display_cols = [
    "Ticker", "Name", "Asset Class", "Sector", "Shares",
    "Cost Price", "Current Price", "Market Value",
    "Weight %", "Unrealised P&L", "Unrealised %", "Daily P&L", "Daily %"
]

def colour_pnl(val):
    if pd.isna(val) or val == 0:
        return ""
    return "color: #00e87a" if val > 0 else "color: #ff4757"

styled = (
    df_filtered[display_cols]
    .style
    .map(colour_pnl, subset=["Unrealised P&L", "Unrealised %", "Daily P&L", "Daily %"])
    .format({
        "Cost Price":     "${:.2f}",
        "Current Price":  "${:.2f}",
        "Market Value":   "${:,.0f}",
        "Unrealised P&L": "${:,.0f}",
        "Unrealised %":   "{:+.2f}%",
        "Daily P&L":      "${:,.0f}",
        "Daily %":        "{:+.2f}%",
        "Weight %":       "{:.2f}%",
    }, na_rep="—")
)

st.dataframe(styled, width="stretch", height=420)
st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🥧 Fund Exposure by Asset Class")
    exposure = df_filtered.groupby("Asset Class")["Market Value"].sum().reset_index()
    fig_pie = px.pie(
        exposure, values="Market Value", names="Asset Class",
        color_discrete_sequence=["#00e87a", "#00c060", "#f5c842", "#ff4757", "#6b8c74"],
        hole=0.4
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8f0ea", margin=dict(t=10, b=10)
    )
    st.plotly_chart(fig_pie, width="stretch")

with col2:
    st.subheader("📊 Unrealised P&L by Holding")
    df_sorted = df_filtered.sort_values("Unrealised P&L", ascending=True).dropna(subset=["Unrealised P&L"])
    colours = ["#ff4757" if v < 0 else "#00e87a" for v in df_sorted["Unrealised P&L"]]
    fig_bar = go.Figure(go.Bar(
        x=df_sorted["Unrealised P&L"],
        y=df_sorted["Ticker"],
        orientation="h",
        marker_color=colours,
        text=df_sorted["Unrealised P&L"].apply(lambda x: f"${x:,.0f}"),
        textposition="outside"
    ))
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8f0ea", margin=dict(t=10, b=10),
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_bar, width="stretch")

# ── Sector Breakdown ──────────────────────────────────────────────────────────
st.subheader("🏭 Sector Exposure")
sector_df = df_filtered.groupby("Sector")["Market Value"].sum().reset_index()
sector_df["Weight %"] = (sector_df["Market Value"] / sector_df["Market Value"].sum() * 100).round(2)
sector_df = sector_df.sort_values("Market Value", ascending=False)

fig_sector = px.bar(
    sector_df, x="Sector", y="Weight %",
    color="Weight %",
    color_continuous_scale=["#1a2d1e", "#00e87a"],
    text=sector_df["Weight %"].apply(lambda x: f"{x:.1f}%")
)
fig_sector.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e8f0ea", margin=dict(t=10, b=10),
    coloraxis_showscale=False,
    xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
)
st.plotly_chart(fig_sector, width="stretch")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "⚠️ Disclaimer: This dashboard is for educational purposes only and does not constitute financial advice. "
    "Prices sourced from Yahoo Finance (15-minute delay). Past performance is not a reliable guide to future performance. "
    "Built by Vrushabh — MSc International Accounting & Finance, Dublin Business School."
)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
