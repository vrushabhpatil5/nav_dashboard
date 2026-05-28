# 📊 Live Fund NAV Dashboard

A real-time (15-min delayed) Fund NAV Dashboard built with Python and Streamlit. Uses a mock diversified portfolio of global equities and ETFs to simulate real-world fund accounting workflows.

Built by **Vrushabh** — MSc International Accounting & Finance, Dublin Business School (First Class Honours).

---

## 🧠 What It Does

This project simulates the core daily workflow of a **fund accountant**:

| Step | What the dashboard does |
|------|------------------------|
| **Security Pricing** | Fetches live prices via Yahoo Finance API |
| **NAV Calculation** | Calculates total fund market value in real time |
| **P&L Attribution** | Shows unrealised gains/losses per holding |
| **Pricing Anomaly Detection** | Flags stale or missing prices before NAV sign-off |
| **Exposure Reporting** | Breaks down fund by asset class and sector |

---

## 📦 Portfolio

A mock portfolio of 15 securities — mix of:
- **Global large-cap equities** (NVIDIA, Apple, Alphabet, Microsoft, Amazon, TSMC, Broadcom, Tesla, Meta, ASML)
- **Global ETFs** (Vanguard VWRL, SPY, QQQ, iShares Emerging Markets, US Aggregate Bond)

> Note: Holdings are chosen for educational diversity across sectors and asset classes. They do not represent any real fund.

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **yfinance** — Yahoo Finance price feeds
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
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
nav-dashboard/
│
├── app.py            # Streamlit dashboard (frontend)
├── nav_engine.py     # NAV calculation engine (core logic)
├── portfolio.py      # Mock fund portfolio configuration
├── requirements.txt  # Python dependencies
└── README.md
```

---

## 📌 Key Features

- ✅ Live price fetching (15-min delay via Yahoo Finance)
- ✅ Real-time NAV calculation
- ✅ Unrealised P&L per holding
- ✅ Daily P&L tracking
- ✅ Pricing anomaly alerts (stale / missing prices)
- ✅ Fund exposure by asset class and sector
- ✅ Auto-refresh every 60 seconds
- ✅ Filter by asset class

---

## ⚠️ Disclaimer

This project is for **educational purposes only** and does not constitute financial advice.
Prices are sourced from Yahoo Finance with a 15-minute delay.
Past performance is not a reliable guide to future performance.

---

## 👤 About

Built as part of a personal finance & data analytics portfolio while job hunting in Dublin, Ireland.

- 🎓 MSc International Accounting & Finance — Dublin Business School (First Class Honours)
- 💼 6+ years in finance operations
- 📍 Based in Dublin, Ireland
- 🔗 [LinkedIn](https://linkedin.com/in/YOUR_PROFILE)
