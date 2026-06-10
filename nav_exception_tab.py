# ─────────────────────────────────────────────────────────────────────────────
# NAV PRICING EXCEPTION REPORT — Tab 2
# Add this to your existing app.py using st.tabs()
#
# HOW TO INTEGRATE:
# 1. Replace your existing page content with:
#    tab1, tab2 = st.tabs(["📊 NAV Dashboard", "🔍 Pricing Exception Report"])
#    with tab1:
#        [paste your existing app.py content here]
#    with tab2:
#        [paste this file's content here]
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import plotly.express as px
import io

def run_pricing_exception_tab():

    st.subheader("🔍 NAV Pricing Exception Report")
    st.caption("Upload any fund holdings CSV · Back-calculate FX rates · Flag exceptions · Reconcile NAV/share")

    # ── Instructions ──────────────────────────────────────────────────────────
    with st.expander("📋 How to use this tool", expanded=False):
        st.markdown("""
        **Step 1 — Prepare your CSV**
        
        Download holdings from any fund provider (iShares, Vanguard, etc.) and ensure it has these columns:
        
        | Column | Description | Example |
        |--------|-------------|---------|
        | `Issuer Ticker` | Security ticker | AAPL |
        | `Name` | Security name | APPLE INC |
        | `Nominal` | Number of shares/units | 239342 |
        | `Price` | Local currency price | 310.26 |
        | `Market Currency` | Currency code | USD |
        | `Market Value` | Official market value in USD | 742583885 |
        | `Weight (%)` | Portfolio weight | 5.08 |
        
        **Step 2 — Enter fund details**
        
        Fill in the fund metadata fields (shares outstanding, published NAV/share, etc.)
        
        **Step 3 — Run the report**
        
        The tool will automatically:
        - Back-calculate FX rates for all non-USD positions
        - Flag exceptions (cash, forwards, futures, zero price)
        - Calculate NAV/share and compare to published figure
        - Show currency exposure breakdown
        """)

    st.divider()

    # ── Fund Metadata Input ────────────────────────────────────────────────────
    st.subheader("📌 Fund Details")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        fund_name = st.text_input("Fund Name", value="iShares Core MSCI World UCITS ETF")
        data_date = st.date_input("Data Date")

    with col_b:
        shares_outstanding = st.number_input(
            "Shares Outstanding",
            value=988572009,
            min_value=1,
            step=1000,
            format="%d"
        )
        published_nav_share = st.number_input(
            "Published NAV/Share (USD)",
            value=143.58,
            min_value=0.0,
            format="%.4f"
        )

    with col_c:
        net_assets_share_class = st.number_input(
            "Net Assets — Share Class (USD)",
            value=141934332215.0,
            min_value=0.0,
            format="%.2f",
            help="From fund factsheet — USD share class only"
        )
        net_assets_fund = st.number_input(
            "Net Assets — Total Fund (USD)",
            value=146167026150.0,
            min_value=0.0,
            format="%.2f",
            help="Total fund assets across all share classes"
        )

    st.divider()

    # ── CSV Upload ─────────────────────────────────────────────────────────────
    st.subheader("📁 Upload Holdings CSV")

    uploaded = st.file_uploader(
        "Upload fund holdings CSV",
        type=["csv"],
        help="Export from iShares, Vanguard, or any fund provider"
    )

    # Sample CSV download
    sample = """Issuer Ticker,Name,Nominal,Price,Market Currency,Market Value,Weight (%)
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
    st.download_button(
        "📥 Download sample CSV",
        data=sample,
        file_name="sample_fund_holdings.csv",
        mime="text/csv"
    )

    if not uploaded:
        st.info("Upload a CSV file to generate the pricing exception report.")
        return

    # ── Parse CSV ──────────────────────────────────────────────────────────────
    try:
        df_raw = pd.read_csv(uploaded)
        df_raw.columns = df_raw.columns.str.strip()
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        return

    # Flexible column name matching
    col_map = {}
    required = {
        "ticker": ["Issuer Ticker", "Ticker", "ticker", "TICKER"],
        "name":   ["Name", "name", "Security Name"],
        "nominal":["Nominal", "nominal", "Shares", "Units"],
        "price":  ["Price", "price", "Local Price"],
        "currency":["Market Currency", "Currency", "Ccy"],
        "market_value":["Market Value", "MarketValue", "MV"],
        "weight": ["Weight (%)", "Weight%", "Weight", "Wt (%)"]
    }

    for key, candidates in required.items():
        for c in candidates:
            if c in df_raw.columns:
                col_map[key] = c
                break

    missing_cols = [k for k in ["ticker","name","nominal","price","currency","market_value"] if k not in col_map]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}. Found: {list(df_raw.columns)}")
        return

    # Build working dataframe
    df = pd.DataFrame()
    df["Ticker"]    = df_raw[col_map["ticker"]].astype(str).str.strip()
    df["Name"]      = df_raw[col_map["name"]].astype(str).str.strip()
    df["Nominal"]   = pd.to_numeric(df_raw[col_map["nominal"]], errors="coerce")
    df["Price"]     = pd.to_numeric(df_raw[col_map["price"]], errors="coerce")
    df["Currency"]  = df_raw[col_map["currency"]].astype(str).str.strip().str.upper()
    df["Market Value"] = pd.to_numeric(df_raw[col_map["market_value"]], errors="coerce")

    if "weight" in col_map:
        df["Weight (%)"] = pd.to_numeric(df_raw[col_map["weight"]], errors="coerce")
    else:
        total_mv = df["Market Value"].sum()
        df["Weight (%)"] = (df["Market Value"] / total_mv * 100).round(4)

    st.success(f"✅ Loaded {len(df):,} positions from CSV.")

    # ── FX Rate Back-Calculation ───────────────────────────────────────────────
    def calc_fx_rate(row):
        try:
            if row["Currency"] == "USD":
                return 1.0
            local_mv = row["Nominal"] * row["Price"]
            if local_mv == 0 or pd.isna(local_mv):
                return 0.0
            return row["Market Value"] / local_mv
        except:
            return None

    df["FX Rate"] = df.apply(calc_fx_rate, axis=1)

    # Price in USD
    def calc_price_usd(row):
        try:
            if row["Currency"] == "USD":
                return row["Price"]
            if row["FX Rate"] and row["FX Rate"] != 0:
                return row["Price"] * row["FX Rate"]
            return None
        except:
            return None

    df["Price (USD)"] = df.apply(calc_price_usd, axis=1)

    # ── Exception Flagging ─────────────────────────────────────────────────────
    def flag_exception(row):
        fx = row["FX Rate"]
        mv = row["Market Value"]
        price = row["Price"]
        ccy = row["Currency"]
        nominal = row["Nominal"]
        name = str(row["Name"]).upper()
        ticker = str(row["Ticker"]).upper()

        # Zero price / zero nominal → DIV/0 scenario
        if pd.isna(fx) or (nominal == 0 and price == 0):
            return "FLAG — Zero Price / Nominal"

        # Futures — zero market value with non-zero price
        if mv == 0 and price > 0:
            return "FLAG — Futures Zero MV"

        # FX forwards — tiny or negative MV relative to position size
        if ccy == "USD" and pd.notna(mv) and pd.notna(nominal) and nominal > 1000 and abs(mv) < 1000:
            return "FLAG — FX Forward / Hedge"

        # Cash positions — FX rate ~0.01 (price quoted in base units × 100)
        if pd.notna(fx) and fx < 0.1:
            return "FLAG — Cash Position"

        # FX forwards identified by name/ticker
        if any(x in name for x in ["CASH", "USD CASH", "EUR CASH", "GBP CASH", "JPY CASH", "CAD CASH"]):
            return "FLAG — Cash Position"

        if "/" in ticker or "FWD" in name or "FORWARD" in name:
            return "FLAG — FX Forward / Hedge"

        # All good
        return "OK"

    df["Comment"] = df.apply(flag_exception, axis=1)

    # ── NAV Calculations ───────────────────────────────────────────────────────
    total_nav = df["Market Value"].sum()
    calc_nav_share = total_nav / shares_outstanding if shares_outstanding > 0 else 0
    nav_gap = calc_nav_share - published_nav_share
    nav_gap_pct = (nav_gap / published_nav_share * 100) if published_nav_share > 0 else 0
    fund_nav_match_pct = abs((total_nav - net_assets_fund) / net_assets_fund * 100) if net_assets_fund > 0 else None

    # ── Summary Dashboard ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Fund Overview")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Fund", fund_name[:30] + "..." if len(fund_name) > 30 else fund_name)
        st.metric("Data Date", str(data_date))
    with k2:
        st.metric("Total Positions", f"{len(df):,}")
        st.metric("Total NAV (USD)", f"${total_nav:,.0f}")
    with k3:
        st.metric("Calculated NAV/Share", f"${calc_nav_share:.4f}")
        st.metric("Published NAV/Share", f"${published_nav_share:.4f}")
    with k4:
        gap_color = "normal" if abs(nav_gap_pct) < 5 else "inverse"
        st.metric(
            "NAV/Share Gap",
            f"${nav_gap:+.4f}",
            f"{nav_gap_pct:+.2f}%",
        )
        if fund_nav_match_pct is not None:
            st.metric("Fund NAV Match", f"{fund_nav_match_pct:.2f}% diff")

    # Gap explanation
    if abs(nav_gap_pct) < 1:
        st.markdown('<div class="ok-box">✅ NAV/share gap is within 1% — likely rounding or intraday timing.</div>', unsafe_allow_html=True)
    elif abs(nav_gap) > 0 and net_assets_share_class < net_assets_fund:
        share_class_nav = net_assets_share_class / shares_outstanding
        st.markdown(
            f'<div class="info-box">ℹ️ Gap explained by multiple share classes. '
            f'Published NAV/share uses USD share class only (${net_assets_share_class/1e9:.2f}bn) '
            f'vs total fund assets (${net_assets_fund/1e9:.2f}bn). '
            f'USD share class NAV/share = ${share_class_nav:.4f}.</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="alert-box">⚠️ NAV/share gap of {nav_gap_pct:+.2f}% — investigate pricing source or share class differences.</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # ── Exception Summary ──────────────────────────────────────────────────────
    st.subheader("🚨 Exception Summary")

    counts = df["Comment"].value_counts().reset_index()
    counts.columns = ["Flag", "Count"]
    counts["% of Holdings"] = (counts["Count"] / len(df) * 100).round(2)

    e1, e2, e3, e4, e5 = st.columns(5)
    ok_count = counts[counts["Flag"] == "OK"]["Count"].sum() if "OK" in counts["Flag"].values else 0
    cash_count = counts[counts["Flag"] == "FLAG — Cash Position"]["Count"].sum() if "FLAG — Cash Position" in counts["Flag"].values else 0
    fwd_count = counts[counts["Flag"] == "FLAG — FX Forward / Hedge"]["Count"].sum() if "FLAG — FX Forward / Hedge" in counts["Flag"].values else 0
    fut_count = counts[counts["Flag"] == "FLAG — Futures Zero MV"]["Count"].sum() if "FLAG — Futures Zero MV" in counts["Flag"].values else 0
    zero_count = counts[counts["Flag"] == "FLAG — Zero Price / Nominal"]["Count"].sum() if "FLAG — Zero Price / Nominal" in counts["Flag"].values else 0

    with e1:
        st.metric("✅ Validated OK", f"{ok_count:,}", f"{ok_count/len(df)*100:.1f}%")
    with e2:
        st.metric("🏦 Cash Positions", cash_count)
    with e3:
        st.metric("🔄 FX Forwards", fwd_count)
    with e4:
        st.metric("📈 Futures Zero MV", fut_count)
    with e5:
        st.metric("❌ Zero Price", zero_count)

    st.divider()

    # ── Currency Exposure ──────────────────────────────────────────────────────
    st.subheader("🌍 Currency Exposure")

    ccy_df = df[df["Comment"] == "OK"].groupby("Currency").agg(
        Count=("Ticker", "count"),
        Total_MV=("Market Value", "sum")
    ).reset_index()
    ccy_df["% of NAV"] = (ccy_df["Total_MV"] / total_nav * 100).round(2)
    ccy_df = ccy_df.sort_values("Total_MV", ascending=False)
    ccy_df.columns = ["Currency", "Count", "Total Market Value (USD)", "% of NAV"]

    c_chart, c_table = st.columns([1, 1])

    with c_chart:
        fig = px.pie(
            ccy_df,
            values="Total Market Value (USD)",
            names="Currency",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e8f0ea",
            margin=dict(t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c_table:
        st.dataframe(
            ccy_df.style.format({
                "Total Market Value (USD)": "${:,.0f}",
                "% of NAV": "{:.2f}%"
            }),
            hide_index=True,
            use_container_width=True,
            height=350
        )

    st.divider()

    # ── Full Exception Report Table ────────────────────────────────────────────
    st.subheader("📋 Full Pricing Exception Report")

    # Colour code by comment
    def colour_comment(val):
        if val == "OK":
            return "color: #00e87a"
        elif "Cash" in str(val):
            return "color: #4a90e2"
        elif "Forward" in str(val) or "Hedge" in str(val):
            return "color: #a78bfa"
        elif "Futures" in str(val):
            return "color: #f5c842"
        elif "Zero" in str(val):
            return "color: #ff4757"
        return ""

    display_df = df[["Ticker", "Name", "Nominal", "Price", "Currency", "FX Rate", "Price (USD)", "Market Value", "Weight (%)", "Comment"]].copy()

    filter_options = ["All"] + sorted(df["Comment"].unique().tolist())
    selected_filter = st.selectbox("Filter by exception type:", filter_options)

    if selected_filter != "All":
        display_df = display_df[display_df["Comment"] == selected_filter]

    styled = display_df.style.map(colour_comment, subset=["Comment"]).format({
        "Nominal": "{:,.0f}",
        "Price": "{:,.4f}",
        "FX Rate": "{:.6f}",
        "Price (USD)": "{:,.4f}",
        "Market Value": "${:,.2f}",
        "Weight (%)": "{:.4f}%"
    }, na_rep="—")

    st.dataframe(styled, use_container_width=True, height=450)

    st.divider()

    # ── Download Report ────────────────────────────────────────────────────────
    st.subheader("📥 Download Report")

    csv_out = display_df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download Exception Report CSV",
        data=csv_out,
        file_name=f"nav_exception_report_{data_date}.csv",
        mime="text/csv"
    )

    st.caption(
        f"Report generated for {fund_name} · {data_date} · "
        f"{len(df):,} positions · Built by Vrushabh · MSc International Accounting & Finance · Dublin"
    )
