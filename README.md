# 📊 Live Fund NAV Dashboard

A real-time (15-min delayed) Fund NAV Dashboard built with Python and Streamlit. Simulates real-world fund accounting workflows across a **45-holding, multi-currency global portfolio**.

🔗 **Live Demo:** https://vrushabhpatil5-nav-dashboard.streamlit.app/

Built by **Vrushabh Patil** — MSc International Accounting & Finance, Dublin Business School (First Class Honours)

---

## 🧠 What It Does

This project simulates the core daily workflow of a **fund accountant**:

| Step | What the dashboard does |
|------|------------------------|
| **Security Pricing** | Fetches live prices via Yahoo Finance API with stale/missing fallbacks |
| **FX Conversion** | Live FX rates across USD, EUR, GBP, JPY, CHF with switchable reporting currency |
| **NAV Calculation** | Calculates total fund market value in real time |
| **P&L Attribution** | Shows unrealised and daily gains/losses per holding |
| **Pricing Anomaly Detection** | Flags stale or missing prices before NAV sign-off |
| **Exposure Reporting** | Breaks down fund by asset class, sector, and currency |
| **CSV Upload** | Upload your own portfolio CSV and price it instantly |

---

## 📦 Portfolio

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
git clone https://github.com/YOUR_USERNAME/nav-dashboard.git
cd nav-dashboard

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
├── app.py                 # Streamlit dashboard + CSV upload
├── nav_engine.py          # NAV engine — pricing, FX, P&L logic
├── portfolio.py           # Default portfolio + FX config
├── requirements.txt       # Python dependencies
├── sample_portfolio.csv   # Template CSV for custom portfolios
└── README.md
```

---

## 📌 Key Features

- ✅ Live price fetching (15-min delay via Yahoo Finance)
- ✅ Multi-currency support — USD, EUR, GBP, JPY, CHF
- ✅ Switchable reporting currency (convert entire NAV to any base currency)
- ✅ Live FX rate panel with stale rate detection
- ✅ Real-time NAV calculation
- ✅ Unrealised & daily P&L per holding
- ✅ Pricing anomaly alerts (stale / missing prices)
- ✅ LSE pence-to-GBP auto correction
- ✅ ADR fallback for Swiss, Japanese & European tickers
- ✅ Currency exposure breakdown chart
- ✅ Fund exposure by asset class and sector
- ✅ CSV upload — bring your own portfolio
- ✅ Auto-refresh every 60 seconds
- ✅ Filter by asset class (Equity, ETF, Bond ETF, Commodity, REIT)

---

## ⚠️ Disclaimer

This project is for **educational purposes only** and does not constitute financial advice.
Prices are sourced from Yahoo Finance with a 15-minute delay. FX rates via Yahoo Finance.
Past performance is not a reliable guide to future performance.

---

## 👤 About

Built as part of a personal finance & data analytics portfolio while job hunting in Dublin, Ireland.

- 🎓 MSc International Accounting & Finance — Dublin Business School (First Class Honours)
- 💼 6+ years in finance operations (AP, ERP, MIS, reconciliations)
- 📍 Based in Dublin, Ireland | Stamp 1G — no sponsorship required
- 🔗 [LinkedIn](https://www.linkedin.com/in/vrushabhpatil-finance)
- 🔗 [Live Dashboard](https://vrushabhpatil5-nav-dashboard.streamlit.app/)
