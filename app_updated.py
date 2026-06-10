# app.py
# Live Fund NAV Dashboard — Streamlit Frontend (with FX support + Pricing Exception Report)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import time
from nav_engine import fetch_prices, fetch_fx_rates, calculate_nav, get_fund_summary
from portfolio import PORTFOLIO, FUND_NAME, SUPPORTED_CURRENCIES

REQUIRED_COLUMNS = {"ticker", "name", "shares", "cost_price", "asset_class", "sector"}
CCY_SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CHF": "Fr"}

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="NAV Dashboard", page_icon="📊", layout="wide")

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
.fx-box {
    background: #1e1a2d; border-left: 4px solid #a78bfa;
    padding: 10px 16px; border-radius: 4px; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Live NAV Dashboard", "🔍 Pricing Exception Report"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXISTING NAV DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    st.title(f"📊 {FUND_NAME}")
    st.caption("Live NAV Dashboard · Prices via Yahoo Finance (15-min delay) · For educational purposes only")

    # ── Sidebar ───────────────────────────────────────────────────────────────
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
            uploaded_file = st.file_uploader("Upload portfolio CSV", type=["csv"])
            st.markdown('<div class="info-box">💡 Download the sample CSV below to get started.</div>', unsafe_allow_html=True)

        st.divider()

        st.header("💱 FX Settings")
        reporting_ccy = st.selectbox(
            "Reporting Currency",
            options=SUPPORTED_CURRENCIES,
            index=0,
            help="All NAV values will be converted to this currency"
        )
        ccy_symbol = CCY_SYMBOLS.get(reporting_ccy, reporting_ccy)
        st.caption(f"NAV will be shown in **{reporting_ccy}** ({ccy_symbol})")

        st.divider()
        st.header("⚙️ Controls")
        auto_refresh = st.toggle("Auto-refresh (60s)", value=False)
        refresh_btn = st.button("🔄 Refresh Now", use_container_width=True)

        st.divider()
        st.subheader("🔍 Filter")
        all_asset_classes = ["Equity", "ETF", "Bond ETF", "Commodity", "REIT"]
        asset_filter = st.multiselect(
            "Asset Class",
            options=all_asset_classes,
            default=all_asset_classes
        )

        st.divider()
        st.caption("Built by Vrushabh · MSc International Accounting & Finance · Dublin Business School")

        sample_csv = """ticker,name,shares,cost_price,asset_class,sector,currency
NVDA,NVIDIA Corp,150,80.00,Equity,Information Technology,USD
AAPL,Apple Inc,200,150.00,Equity,Information Technology,USD
GOOGL,Alphabet Inc,180,120.00,Equity,Communication Services,USD
MSFT,Microsoft Corp,120,280.00,Equity,Information Technology,USD
AMZN,Amazon.com Inc,130,130.00,Equity,Consumer Discretionary,USD
TSM,Taiwan Semiconductor,200,90.00,Equity,Information Technology,USD
AVGO,Broadcom Inc,80,550.00,Equity,Information Technology,USD
TSLA,Tesla Inc,160,200.00,Equity,Consumer Discretionary,USD
META,Meta Platforms Inc,100,250.00,Equity,Communication Services,USD
ASML,ASML Holding NV,40,600.00,Equity,Information Technology,EUR
SPY,SPDR S&P 500 ETF,300,420.00,ETF,US Equity,USD
QQQ,Invesco QQQ Nasdaq 100,150,350.00,ETF,US Tech Equity,USD
IEMG,iShares MSCI Emerging Mkts,400,48.00,ETF,Emerging Markets,USD
AGG,iShares US Aggregate Bond,300,96.00,Bond ETF,Fixed Income,USD
VWRL.L,Vanguard FTSE All-World ETF,500,95.00,ETF,Global Equity,GBP
"""
        st.download_button(
            label="📥 Download Sample CSV",
            data=sample_csv,
            file_name="sample_portfolio.csv",
            mime="text/csv",
        )
        st.divider()

    # ── Load portfolio ─────────────────────────────────────────────────────────
    def load_portfolio_from_csv(file):
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip().str.lower()
            missing = REQUIRED_COLUMNS - set(df.columns)
            if missing:
                st.error(f"❌ Missing columns in CSV: {', '.join(missing)}")
                return None
            df["shares"] = pd.to_numeric(df["shares"], errors="coerce")
            df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce")
            if "currency" not in df.columns:
                df["currency"] = "USD"
            invalid = df[df["shares"].isna() | df["cost_price"].isna()]
            if not invalid.empty:
                st.warning(f"⚠️ {len(invalid)} row(s) skipped due to invalid values.")
            df = df.dropna(subset=["shares", "cost_price"])
            if df.empty:
                st.error("❌ No valid rows found in CSV.")
                return None
            return df.to_dict(orient="records")
        except Exception as e:
            st.error(f"❌ Could not read CSV: {e}")
            return None

    if portfolio_mode == "Upload CSV file" and uploaded_file:
        portfolio = load_portfolio_from_csv(uploaded_file)
        if portfolio is None:
            st.stop()
        st.markdown(f'<div class="ok-box">✅ CSV loaded — <b>{len(portfolio)} holdings</b> found.</div>', unsafe_allow_html=True)
    else:
        portfolio = PORTFOLIO

    if portfolio_mode == "Upload CSV file" and not uploaded_file:
        st.markdown('<div class="info-box">📁 No CSV uploaded — showing default portfolio.</div>', unsafe_allow_html=True)

    @st.cache_data(ttl=60)
    def load_data(portfolio_key, portfolio_data, rep_ccy):
        tickers = [h["ticker"] for h in portfolio_data]
        prices = fetch_prices(tickers)
        fx_rates = fetch_fx_rates(rep_ccy, portfolio_data)
        df = calculate_nav_from_portfolio(prices, portfolio_data, rep_ccy, fx_rates)
        summary = get_fund_summary(df, rep_ccy)
        return df, summary, fx_rates

    LSE_PENCE_TICKERS = {"SHEL.L", "AZN.L", "HSBA.L", "RIO.L", "ULVR.L", "BP.L", "GSK.L", "BATS.L"}

    def calculate_nav_from_portfolio(price_data, portfolio_data, reporting_ccy, fx_rates):
        rows = []
        for holding in portfolio_data:
            ticker = str(holding["ticker"]).strip().upper()
            px = price_data.get(ticker, {"price": None, "prev_close": None, "stale": True, "missing": True, "fetched_at": "—"})
            local_ccy = str(holding.get("currency", "USD")).strip().upper()
            current_price = px.get("price")
            prev_close = px.get("prev_close")
            cost_price = float(holding["cost_price"])
            shares = float(holding["shares"])
            if ticker in LSE_PENCE_TICKERS and current_price and current_price > 500:
                current_price = current_price / 100
                prev_close = prev_close / 100 if prev_close else None
            if px.get("used_fallback"):
                local_ccy = "USD"
            fx_info = fx_rates.get(local_ccy, {"rate": 1.0, "stale": False})
            fx_rate = fx_info.get("rate") or 1.0
            fx_stale = fx_info.get("stale", False)
            local_mv = round(current_price * shares, 2) if current_price is not None else None
            local_cost_basis = round(cost_price * shares, 2)
            market_value = round(local_mv * fx_rate, 2) if local_mv is not None else None
            cost_basis = round(local_cost_basis * fx_rate, 2)
            unrealised_pnl = round(market_value - cost_basis, 2) if market_value is not None else None
            unrealised_pct = round((unrealised_pnl / cost_basis) * 100, 2) if unrealised_pnl is not None and cost_basis else None
            daily_pnl, daily_pct = None, None
            if current_price is not None and prev_close is not None:
                daily_pnl = round((current_price - prev_close) * shares * fx_rate, 2)
                daily_pct = round(((current_price - prev_close) / prev_close) * 100, 2) if prev_close != 0 else None
            rows.append({
                "Ticker": ticker, "Name": holding.get("name", ticker),
                "Asset Class": holding.get("asset_class", "—"), "Sector": holding.get("sector", "—"),
                "Currency": local_ccy, "FX Rate": fx_rate, "FX Stale": fx_stale,
                "Shares": shares, "Cost Price": cost_price, "Current Price": current_price,
                "Local MV": local_mv, "Cost Basis": cost_basis, "Market Value": market_value,
                "Unrealised P&L": unrealised_pnl, "Unrealised %": unrealised_pct,
                "Daily P&L": daily_pnl, "Daily %": daily_pct,
                "Stale Price": px.get("stale", False), "Missing Price": px.get("missing", False),
                "Price As At": px.get("fetched_at", "—"),
            })
        df = pd.DataFrame(rows)
        total_mv = df["Market Value"].sum()
        df["Weight %"] = df["Market Value"].apply(lambda mv: round((mv / total_mv) * 100, 2) if total_mv and mv else None)
        return df

    if refresh_btn:
        st.cache_data.clear()

    portfolio_key = str([(h["ticker"], h["shares"], h["cost_price"]) for h in portfolio])
    df, summary, fx_rates = load_data(portfolio_key, portfolio, reporting_ccy)
    df_filtered = df[df["Asset Class"].isin(asset_filter)] if asset_filter else df
    sym = ccy_symbol

    st.subheader("💱 Live FX Rates")
    fx_cols = st.columns(len(fx_rates))
    for i, (ccy, info) in enumerate(sorted(fx_rates.items())):
        rate = info.get("rate")
        stale = info.get("stale", False)
        label = f"{ccy} → {reporting_ccy}"
        with fx_cols[i]:
            if ccy == reporting_ccy:
                st.metric(label, "1.0000", help="Base currency")
            elif rate:
                st.metric(label, f"{rate:.4f}", help="⚠️ Stale FX rate" if stale else "Live rate")
            else:
                st.metric(label, "N/A", help="Could not fetch rate")

    if summary.get("fx_stale", 0) > 0:
        st.markdown(f'<div class="fx-box">⚠️ {summary["fx_stale"]} FX rate(s) may be stale. Review before NAV sign-off.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ok-box">✅ All FX rates loaded successfully ({reporting_ccy} reporting basis).</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("📌 Fund NAV Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total NAV", f"{sym}{summary['nav']:,.0f}", help=f"Reporting currency: {reporting_ccy}")
    with c2: st.metric("Unrealised P&L", f"{sym}{summary['unrealised_pnl']:,.0f}", f"{summary['unrealised_pct']:+.2f}%")
    with c3: st.metric("Daily P&L", f"{sym}{summary['daily_pnl']:,.0f}")
    with c4: st.metric("Holdings", summary['num_holdings'])
    with c5:
        alert_color = "🔴" if summary['pricing_alerts'] > 0 else "🟢"
        st.metric(f"{alert_color} Pricing Alerts", summary['pricing_alerts'])
    st.caption(f"Last calculated: {summary['last_calculated']} · Reporting in **{reporting_ccy}**")

    st.divider()
    alerts = df[df["Stale Price"] | df["Missing Price"]]
    if not alerts.empty:
        st.subheader("⚠️ Pricing Alerts")
        for _, row in alerts.iterrows():
            reason = "Missing price" if row["Missing Price"] else "Stale price"
            st.markdown(f'<div class="alert-box">⚠️ <b>{row["Ticker"]} — {row["Name"]}</b>: {reason}. Using fallback (prev close). Review before NAV sign-off.</div>', unsafe_allow_html=True)
        st.divider()
    else:
        st.markdown('<div class="ok-box">✅ All prices validated. No anomalies detected.</div>', unsafe_allow_html=True)
        st.divider()

    st.subheader("📋 Holdings Breakdown")
    display_cols = ["Ticker", "Name", "Asset Class", "Sector", "Currency", "FX Rate", "Shares", "Cost Price", "Current Price", "Local MV", "Market Value", "Weight %", "Unrealised P&L", "Unrealised %", "Daily P&L", "Daily %"]

    def colour_pnl(val):
        if pd.isna(val) or val == 0: return ""
        return "color: #00e87a" if val > 0 else "color: #ff4757"

    styled = (
        df_filtered[display_cols].style
        .map(colour_pnl, subset=["Unrealised P&L", "Unrealised %", "Daily P&L", "Daily %"])
        .format({"Cost Price": "${:.2f}", "Current Price": "${:.2f}", "Local MV": "${:,.0f}", "Market Value": f"{sym}{{:,.0f}}", "Unrealised P&L": f"{sym}{{:,.0f}}", "Unrealised %": "{:+.2f}%", "Daily P&L": f"{sym}{{:,.0f}}", "Daily %": "{:+.2f}%", "Weight %": "{:.2f}%", "FX Rate": "{:.4f}"}, na_rep="—")
    )
    st.dataframe(styled, use_container_width=True, height=420)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🥧 Fund Exposure by Asset Class")
        exposure = df_filtered.groupby("Asset Class")["Market Value"].sum().reset_index()
        fig_pie = px.pie(exposure, values="Market Value", names="Asset Class", color_discrete_sequence=["#00e87a", "#00c060", "#f5c842", "#ff4757", "#6b8c74"], hole=0.4)
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8f0ea", margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("📊 Unrealised P&L by Holding")
        df_sorted = df_filtered.sort_values("Unrealised P&L", ascending=True).dropna(subset=["Unrealised P&L"])
        colours = ["#ff4757" if v < 0 else "#00e87a" for v in df_sorted["Unrealised P&L"]]
        fig_bar = go.Figure(go.Bar(x=df_sorted["Unrealised P&L"], y=df_sorted["Ticker"], orientation="h", marker_color=colours, text=df_sorted["Unrealised P&L"].apply(lambda x: f"{sym}{x:,.0f}"), textposition="outside"))
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8f0ea", margin=dict(t=10, b=10), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig_bar, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🌍 Currency Exposure")
        ccy_df = df_filtered.groupby("Currency")["Market Value"].sum().reset_index()
        ccy_df["Weight %"] = (ccy_df["Market Value"] / ccy_df["Market Value"].sum() * 100).round(2)
        fig_ccy = px.pie(ccy_df, values="Market Value", names="Currency", color_discrete_sequence=["#a78bfa", "#7c3aed", "#60a5fa", "#f59e0b", "#34d399"], hole=0.4)
        fig_ccy.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8f0ea", margin=dict(t=10, b=10))
        st.plotly_chart(fig_ccy, use_container_width=True)
        fx_table = pd.DataFrame([{"Currency": ccy, "Rate vs " + reporting_ccy: info.get("rate", "N/A"), "Status": "⚠️ Stale" if info.get("stale") else "✅ Live"} for ccy, info in fx_rates.items() if ccy != reporting_ccy])
        if not fx_table.empty:
            st.dataframe(fx_table, hide_index=True, use_container_width=True)

    with col4:
        st.subheader("🏭 Sector Exposure")
        sector_df = df_filtered.groupby("Sector")["Market Value"].sum().reset_index()
        sector_df["Weight %"] = (sector_df["Market Value"] / sector_df["Market Value"].sum() * 100).round(2)
        sector_df = sector_df.sort_values("Market Value", ascending=False)
        fig_sector = px.bar(sector_df, x="Sector", y="Weight %", color="Weight %", color_continuous_scale=["#1a2d1e", "#00e87a"], text=sector_df["Weight %"].apply(lambda x: f"{x:.1f}%"))
        fig_sector.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8f0ea", margin=dict(t=10, b=10), coloraxis_showscale=False, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
        st.plotly_chart(fig_sector, use_container_width=True)

    st.divider()
    st.caption("⚠️ Disclaimer: This dashboard is for educational purposes only and does not constitute financial advice. Prices sourced from Yahoo Finance (15-minute delay). FX rates via Yahoo Finance. Built by Vrushabh — MSc International Accounting & Finance, Dublin Business School.")

    if auto_refresh:
        time.sleep(60)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — NAV PRICING EXCEPTION REPORT
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    st.subheader("🔍 NAV Pricing Exception Report")
    st.caption("Upload any fund holdings CSV · Back-calculate FX rates · Flag exceptions · Reconcile NAV/share")

    with st.expander("📋 How to use this tool", expanded=False):
        st.markdown("""
        **Step 1 — Prepare your CSV**
        Download holdings from any fund provider and ensure it has these columns:
        `Issuer Ticker`, `Name`, `Nominal`, `Price`, `Market Currency`, `Market Value`, `Weight (%)`

        **Step 2 — Enter fund details manually**
        Fill in shares outstanding, published NAV/share, and net assets from the fund factsheet.

        **Step 3 — Run the report**
        The tool back-calculates FX rates, flags exceptions, and reconciles NAV/share vs published.
        """)

    st.divider()
    st.subheader("📌 Fund Details")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        fund_name = st.text_input("Fund Name", value="iShares Core MSCI World UCITS ETF", key="pe_fund_name")
        data_date = st.date_input("Data Date", key="pe_date")
    with col_b:
        shares_outstanding = st.number_input("Shares Outstanding", value=988572009, min_value=1, step=1000, format="%d", key="pe_shares")
        published_nav_share = st.number_input("Published NAV/Share (USD)", value=143.58, min_value=0.0, format="%.4f", key="pe_nav_share")
    with col_c:
        net_assets_share_class = st.number_input("Net Assets — Share Class (USD)", value=141934332215.0, min_value=0.0, format="%.2f", help="USD share class only", key="pe_sc_assets")
        net_assets_fund = st.number_input("Net Assets — Total Fund (USD)", value=146167026150.0, min_value=0.0, format="%.2f", help="All share classes combined", key="pe_fund_assets")

    st.divider()
    st.subheader("📁 Upload Holdings CSV")

    sample_holdings = """Issuer Ticker,Name,Nominal,Price,Market Currency,Market Value,Weight (%)
NVDA,NVIDIA CORP,37634819,214.75,USD,8082077380.25,5.53
AAPL,APPLE INC,23934245,310.26,USD,7425838853.70,5.08
MSFT,MICROSOFT CORP,11500500,427.34,USD,4914623670.00,3.36
ASML,ASML HOLDING NV,632787,1724.53,EUR,1091266480.32,0.75
NESN,NESTLE SA,4168922,97.80,CHF,407738141.06,0.28
7203,TOYOTA MOTOR CORP,15092000,18.01,JPY,2718437713.00,0.19
HSBA,HSBC HOLDINGS PLC,27780567,18.70,GBP,5195968351.00,0.36
JPY CASH,JPY CASH,1143436899,0.63,JPY,7148938.00,0.05
EUR/USD,EUR/USD FWD,4677896,1.00,USD,-3789.10,0.00
ESM6,S&P500 EMINI JUN 26,931,7571.75,USD,0.00,0.00
"""
    st.download_button("📥 Download sample CSV", data=sample_holdings, file_name="sample_fund_holdings.csv", mime="text/csv", key="pe_sample_dl")

    pe_upload = st.file_uploader("Upload fund holdings CSV", type=["csv"], key="pe_upload")

    if not pe_upload:
        st.info("Upload a CSV file to generate the pricing exception report.")
    else:
        try:
            df_raw = pd.read_csv(pe_upload)
            df_raw.columns = df_raw.columns.str.strip()
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
            st.stop()

        col_map = {}
        required = {
            "ticker":       ["Issuer Ticker", "Ticker", "ticker"],
            "name":         ["Name", "name", "Security Name"],
            "nominal":      ["Nominal", "nominal", "Shares", "Units"],
            "price":        ["Price", "price", "Local Price"],
            "currency":     ["Market Currency", "Currency", "Ccy"],
            "market_value": ["Market Value", "MarketValue", "MV"],
            "weight":       ["Weight (%)", "Weight%", "Weight", "Wt (%)"]
        }
        for key, candidates in required.items():
            for c in candidates:
                if c in df_raw.columns:
                    col_map[key] = c
                    break

        missing_cols = [k for k in ["ticker","name","nominal","price","currency","market_value"] if k not in col_map]
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}. Found: {list(df_raw.columns)}")
            st.stop()

        df = pd.DataFrame()
        df["Ticker"]       = df_raw[col_map["ticker"]].astype(str).str.strip()
        df["Name"]         = df_raw[col_map["name"]].astype(str).str.strip()
        df["Nominal"]      = pd.to_numeric(df_raw[col_map["nominal"]], errors="coerce")
        df["Price"]        = pd.to_numeric(df_raw[col_map["price"]], errors="coerce")
        df["Currency"]     = df_raw[col_map["currency"]].astype(str).str.strip().str.upper()
        df["Market Value"] = pd.to_numeric(df_raw[col_map["market_value"]], errors="coerce")

        if "weight" in col_map:
            df["Weight (%)"] = pd.to_numeric(df_raw[col_map["weight"]], errors="coerce")
        else:
            total_mv_raw = df["Market Value"].sum()
            df["Weight (%)"] = (df["Market Value"] / total_mv_raw * 100).round(4)

        st.success(f"✅ Loaded {len(df):,} positions.")

        # FX Rate back-calculation
        def calc_fx(row):
            try:
                if row["Currency"] == "USD": return 1.0
                local_mv = row["Nominal"] * row["Price"]
                if local_mv == 0 or pd.isna(local_mv): return 0.0
                return row["Market Value"] / local_mv
            except: return None

        df["FX Rate"] = df.apply(calc_fx, axis=1)

        def calc_price_usd(row):
            try:
                if row["Currency"] == "USD": return row["Price"]
                if row["FX Rate"] and row["FX Rate"] != 0: return row["Price"] * row["FX Rate"]
                return None
            except: return None

        df["Price (USD)"] = df.apply(calc_price_usd, axis=1)

        # Exception flagging
        def flag(row):
            fx = row["FX Rate"]
            mv = row["Market Value"]
            price = row["Price"]
            ccy = row["Currency"]
            nominal = row["Nominal"]
            name = str(row["Name"]).upper()
            ticker = str(row["Ticker"]).upper()
            if pd.isna(fx) or (nominal == 0 and price == 0): return "FLAG — Zero Price / Nominal"
            if mv == 0 and price > 0: return "FLAG — Futures Zero MV"
            if ccy == "USD" and pd.notna(mv) and pd.notna(nominal) and nominal > 1000 and abs(mv) < 1000: return "FLAG — FX Forward / Hedge"
            if pd.notna(fx) and fx < 0.1: return "FLAG — Cash Position"
            if any(x in name for x in ["CASH"]): return "FLAG — Cash Position"
            if "/" in ticker or "FWD" in name or "FORWARD" in name: return "FLAG — FX Forward / Hedge"
            return "OK"

        df["Comment"] = df.apply(flag, axis=1)

        # NAV calculations
        total_nav = df["Market Value"].sum()
        calc_nav_share = total_nav / shares_outstanding if shares_outstanding > 0 else 0
        nav_gap = calc_nav_share - published_nav_share
        nav_gap_pct = (nav_gap / published_nav_share * 100) if published_nav_share > 0 else 0
        fund_match_pct = abs((total_nav - net_assets_fund) / net_assets_fund * 100) if net_assets_fund > 0 else None

        st.divider()
        st.subheader("📊 Fund Overview")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Positions", f"{len(df):,}")
            st.metric("Total NAV (USD)", f"${total_nav:,.0f}")
        with k2:
            st.metric("Calculated NAV/Share", f"${calc_nav_share:.4f}")
            st.metric("Published NAV/Share", f"${published_nav_share:.4f}")
        with k3:
            st.metric("NAV/Share Gap", f"${nav_gap:+.4f}", f"{nav_gap_pct:+.2f}%")
            if fund_match_pct is not None:
                st.metric("Fund NAV Match", f"{fund_match_pct:.2f}% diff")
        with k4:
            ok_n = len(df[df["Comment"] == "OK"])
            flag_n = len(df[df["Comment"] != "OK"])
            st.metric("✅ Validated OK", f"{ok_n:,}", f"{ok_n/len(df)*100:.1f}%")
            st.metric("⚠️ Flagged", f"{flag_n:,}", f"{flag_n/len(df)*100:.1f}%")

        if abs(nav_gap_pct) < 1:
            st.markdown('<div class="ok-box">✅ NAV/share gap within 1% — rounding or intraday timing.</div>', unsafe_allow_html=True)
        elif net_assets_share_class < net_assets_fund:
            sc_nav = net_assets_share_class / shares_outstanding
            st.markdown(f'<div class="info-box">ℹ️ Gap explained by multiple share classes. Published NAV uses USD share class (${net_assets_share_class/1e9:.2f}bn) vs total fund (${net_assets_fund/1e9:.2f}bn). USD class NAV/share = ${sc_nav:.4f}.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-box">⚠️ Gap of {nav_gap_pct:+.2f}% — investigate pricing or share class differences.</div>', unsafe_allow_html=True)

        st.divider()
        st.subheader("🚨 Exception Summary")
        counts = df["Comment"].value_counts()

        e1, e2, e3, e4, e5 = st.columns(5)
        with e1: st.metric("✅ OK", int(counts.get("OK", 0)), f"{counts.get('OK',0)/len(df)*100:.1f}%")
        with e2: st.metric("🏦 Cash", int(counts.get("FLAG — Cash Position", 0)))
        with e3: st.metric("🔄 FX Forwards", int(counts.get("FLAG — FX Forward / Hedge", 0)))
        with e4: st.metric("📈 Futures", int(counts.get("FLAG — Futures Zero MV", 0)))
        with e5: st.metric("❌ Zero Price", int(counts.get("FLAG — Zero Price / Nominal", 0)))

        st.divider()
        st.subheader("🌍 Currency Exposure")
        ccy_df = df[df["Comment"] == "OK"].groupby("Currency").agg(Count=("Ticker","count"), Total_MV=("Market Value","sum")).reset_index()
        ccy_df["% of NAV"] = (ccy_df["Total_MV"] / total_nav * 100).round(2)
        ccy_df = ccy_df.sort_values("Total_MV", ascending=False)

        cc1, cc2 = st.columns([1,1])
        with cc1:
            fig_ccy = px.pie(ccy_df, values="Total_MV", names="Currency", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
            fig_ccy.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e8f0ea", margin=dict(t=10,b=10))
            st.plotly_chart(fig_ccy, use_container_width=True)
        with cc2:
            st.dataframe(ccy_df.rename(columns={"Total_MV":"Market Value (USD)"}).style.format({"Market Value (USD)":"${:,.0f}","% of NAV":"{:.2f}%"}), hide_index=True, use_container_width=True, height=350)

        st.divider()
        st.subheader("📋 Full Exception Report")

        def colour_flag(val):
            if val == "OK": return "color: #00e87a"
            elif "Cash" in str(val): return "color: #4a90e2"
            elif "Forward" in str(val): return "color: #a78bfa"
            elif "Futures" in str(val): return "color: #f5c842"
            elif "Zero" in str(val): return "color: #ff4757"
            return ""

        filter_opts = ["All"] + sorted(df["Comment"].unique().tolist())
        sel = st.selectbox("Filter by exception type:", filter_opts, key="pe_filter")
        disp = df[["Ticker","Name","Nominal","Price","Currency","FX Rate","Price (USD)","Market Value","Weight (%)","Comment"]].copy()
        if sel != "All":
            disp = disp[disp["Comment"] == sel]

        st.dataframe(
            disp.style.map(colour_flag, subset=["Comment"]).format({
                "Nominal": "{:,.0f}", "Price": "{:,.4f}", "FX Rate": "{:.6f}",
                "Price (USD)": "{:,.4f}", "Market Value": "${:,.2f}", "Weight (%)": "{:.4f}%"
            }, na_rep="—"),
            use_container_width=True, height=450
        )

        st.divider()
        st.subheader("📥 Download Report")
        st.download_button(
            "⬇️ Download Exception Report CSV",
            data=disp.to_csv(index=False),
            file_name=f"nav_exception_report_{data_date}.csv",
            mime="text/csv",
            key="pe_download"
        )
        st.caption(f"Report: {fund_name} · {data_date} · {len(df):,} positions · Built by Vrushabh · MSc International Accounting & Finance · Dublin")
