# 📊 Live Fund NAV Dashboard + Pricing Exception Report

A real-time (15-min delayed) Fund NAV Dashboard built with Python and Streamlit. Simulates real-world fund accounting workflows across a **45-holding, multi-currency global portfolio** — plus a full **NAV Pricing Exception Report tool** built on real iShares MSCI World ETF data.

🔗 **Live Demo:** https://vrushabhpatil5-nav-dashboard.streamlit.app/

Built by **Vrushabh Patil** — MSc International Accounting & Finance, Dublin Business School (First Class Honours)

---

## 🧠 What It Does

This project simulates the core daily workflow of a **fund accountant** across two tabs:

### 📊 Tab 1 — Live NAV Dashboard

| Step | What the dashboard does |
|------|------------------------|
| **Security Pricing** | Fetches live prices via Yahoo Finance API with stale/missing fallbacks |
| **FX Conversion** | Live FX rates across USD, EUR, GBP, JPY, CHF with switchable reporting currency |
| **NAV Calculation** | Calculates total fund market value in real time |
| **P&L Attribution** | Shows unrealised and daily gains/losses per holding |
| **Pricing Anomaly Detection** | Flags stale or missing prices before NAV sign-off |
| **Exposure Reporting** | Breaks down fund by asset class, sector, and currency |
| **CSV Upload** | Upload your own portfolio CSV and price it instantly |

### 🔍 Tab 2 — NAV Pricing Exception Report

Built on real iShares Core MSCI World UCITS ETF data ($146bn, 1,329 positions, 14 currencies):

| Step | What the tool does |
|------|-------------------|
| **CSV Upload** | Upload any fund holdings CSV from any provider |
| **FX Rate Back-Calculation** | Reverse-engineers the FX rate used from market values |
| **Exception Flagging** | Categorises positions — cash, FX forwards, futures, zero price |
| **NAV Reconciliation** | Calculates NAV/share and compares against published figure |
| **Share Class Analysis** | Explains NAV/share gaps using share class vs total fund assets |
| **Currency Exposure** | Breakdown of portfolio by currency with market value and % of NAV |
| **Downloadable Report** | Export full exception report as CSV |

> Validated on iShares Core MSCI World UCITS ETF — 1,329 positions, 14 currencies, NAV matched within 0.03% of published figure.

---

## 🏦 Real-World Context

The iShares Core MSCI World UCITS ETF used in Tab 2 is:
- **Administered by:** State Street Fund Services (Ireland) Limited
- **Custodian:** State Street Custodial Services (Ireland) Limited
- **Total Fund Assets:** $146.17bn (as of 03 June 2026)
- **Domicile:** Ireland (UCITS)

This means the pricing exception workflow in Tab 2 replicates what State Street's fund accounting team performs daily before NAV sign-off.

---

## 📦 Tab 1 Portfolio

A mock portfolio of **45 securities** across 5 currencies and 7 asset classes:

| Asset Class | Examples |
|-------------|---------|
| **US Equities (USD)** | NVIDIA, Apple, Microsoft, JPMorgan, Goldman Sachs, ExxonMobil |
| **European Equities (EUR)** | ASML, SAP, Siemens, Airbus, LVMH, L'Oréal |
| **UK Equities (GBP)** | Shell, AstraZeneca, HSBC, Rio Tinto |
| **Japanese Equities (JPY)** | Toyota, Sony, SoftBank |
| **Swiss Equities (CHF)** | Nestlé, Roche, Novartis |
| **Global ETFs** | SPY, QQQ, VWRL, IEMG, EFA, VWO |
| **Bond ETFs** | AGG, TLT, HYG, EMB |
| **Commodities** | GLD (Gold), SLV (Silver), USO (Oil) |
| **REITs** | VNQ (Vanguard Real Estate) |

> Holdings are chosen for educational diversity. They do not represent any real fund.

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **yfinance** — Yahoo Finance price feeds + FX rates
- **pandas** — NAV and P&L calculations
- **Streamlit** — Live dashboard UI
- **Plotly** — Interactive charts
- **numpy** — Numerical operations

---

## 🚀 How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/vrushabhpatil5/nav_dashboard.git
cd nav_dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dashboard
python -m streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
nav-dashboard/
│
├── app.py                               # Streamlit dashboard — Tab 1 + Tab 2
├── nav_engine.py                        # NAV engine — pricing, FX, P&L logic
├── portfolio.py                         # Default portfolio + FX config
├── requirements.txt                     # Python dependencies
├── sample_portfolio.csv                 # Template CSV for custom portfolios
├── sample_portfolio_multicurrency.csv   # Template CSV for multi-currency portfolios
└── README.md
```

---

## 📌 Key Features

### Tab 1 — Live NAV Dashboard
- ✅ Live price fetching (15-min delay via Yahoo Finance)
- ✅ Multi-currency support — USD, EUR, GBP, JPY, CHF
- ✅ Switchable reporting currency (convert entire NAV to any base currency)
- ✅ Live FX rate panel with stale rate detection
- ✅ Real-time NAV calculation
- ✅ Unrealised & daily P&L per holding
- ✅ Pricing anomaly alerts (stale/missing prices)
- ✅ LSE pence-to-GBP auto correction
- ✅ ADR fallback for Swiss, Japanese & European tickers
- ✅ Currency exposure breakdown chart
- ✅ Fund exposure by asset class and sector
- ✅ CSV upload — bring your own portfolio
- ✅ Auto-refresh every 60 seconds
- ✅ Filter by asset class

### Tab 2 — NAV Pricing Exception Report
- ✅ Upload any fund holdings CSV
- ✅ FX rate back-calculation for all non-USD positions
- ✅ Exception categorisation — cash, FX forwards, futures, zero price
- ✅ NAV/share calculation vs published figure
- ✅ Share class gap analysis and explanation
- ✅ Currency exposure breakdown — count, market value, % of NAV
- ✅ Colour-coded exception table with filter by flag type
- ✅ Downloadable exception report CSV
- ✅ Tested on real iShares MSCI World ETF data — 1,329 positions, 14 currencies

---

## 📊 Tab 2 — Sample Results (iShares Core MSCI World UCITS ETF)

| Metric | Value |
|--------|-------|
| Total Positions | 1,329 |
| Validated OK | 1,294 (97.4%) |
| Cash Positions | 18 |
| FX Forwards | 13 |
| Futures Zero MV | 4 |
| Zero Price | 0 |
| Calculated NAV/Share | $147.94 |
| Published NAV/Share | $143.58 |
| NAV Gap Explanation | Multiple share classes — USD class $141.9bn vs total fund $146.2bn |
| Fund NAV Match | Within 0.03% of published net assets |

---

## ⚠️ Disclaimer

This project is for **educational purposes only** and does not constitute financial advice.
Prices are sourced from Yahoo Finance with a 15-minute delay. FX rates via Yahoo Finance.
iShares data used for educational demonstration only.

---

## 👤 About

Built as part of a personal finance and data analytics portfolio while job hunting in Dublin, Ireland.

- 🎓 MSc International Accounting & Finance — Dublin Business School (First Class Honours)
- 💼 6+ years in finance operations (AP, ERP, MIS, reconciliations)
- 📍 Based in Dublin, Ireland
- 🔗 [LinkedIn](https://www.linkedin.com/in/vrushabh-patil-finance/)
- 🔗 [Live Dashboard](https://vrushabhpatil5-nav-dashboard.streamlit.app/)
