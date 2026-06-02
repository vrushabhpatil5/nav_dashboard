# portfolio.py
# Mock Fund Portfolio — Mix of EMPOWER Top Holdings + Global ETFs

FUND_NAME = "NAV Dashboard"

PORTFOLIO = [
    # --- EMPOWER Top Share Holdings ---
    {"ticker": "NVDA",   "name": "NVIDIA Corp",                     "shares": 150,  "cost_price": 80.00,  "asset_class": "Equity",   "sector": "Information Technology",  "currency": "USD"},
    {"ticker": "AAPL",   "name": "Apple Inc",                       "shares": 200,  "cost_price": 150.00, "asset_class": "Equity",   "sector": "Information Technology",  "currency": "USD"},
    {"ticker": "GOOGL",  "name": "Alphabet Inc",                    "shares": 180,  "cost_price": 120.00, "asset_class": "Equity",   "sector": "Communication Services",  "currency": "USD"},
    {"ticker": "MSFT",   "name": "Microsoft Corp",                  "shares": 120,  "cost_price": 280.00, "asset_class": "Equity",   "sector": "Information Technology",  "currency": "USD"},
    {"ticker": "AMZN",   "name": "Amazon.com Inc",                  "shares": 130,  "cost_price": 130.00, "asset_class": "Equity",   "sector": "Consumer Discretionary",  "currency": "USD"},
    {"ticker": "TSM",    "name": "Taiwan Semiconductor",            "shares": 200,  "cost_price": 90.00,  "asset_class": "Equity",   "sector": "Information Technology",  "currency": "USD"},
    {"ticker": "AVGO",   "name": "Broadcom Inc",                    "shares": 80,   "cost_price": 550.00, "asset_class": "Equity",   "sector": "Information Technology",  "currency": "USD"},
    {"ticker": "TSLA",   "name": "Tesla Inc",                       "shares": 160,  "cost_price": 200.00, "asset_class": "Equity",   "sector": "Consumer Discretionary",  "currency": "USD"},
    {"ticker": "META",   "name": "Meta Platforms Inc",              "shares": 100,  "cost_price": 250.00, "asset_class": "Equity",   "sector": "Communication Services",  "currency": "USD"},
    {"ticker": "ASML",   "name": "ASML Holding NV",                 "shares": 40,   "cost_price": 600.00, "asset_class": "Equity",   "sector": "Information Technology",  "currency": "EUR"},

    # --- Global ETFs ---
    {"ticker": "VWRL.L", "name": "Vanguard FTSE All-World ETF",     "shares": 500,  "cost_price": 95.00,  "asset_class": "ETF",      "sector": "Global Equity",           "currency": "GBP"},
    {"ticker": "SPY",    "name": "SPDR S&P 500 ETF",                "shares": 300,  "cost_price": 420.00, "asset_class": "ETF",      "sector": "US Equity",               "currency": "USD"},
    {"ticker": "QQQ",    "name": "Invesco QQQ (Nasdaq 100)",        "shares": 150,  "cost_price": 350.00, "asset_class": "ETF",      "sector": "US Tech Equity",          "currency": "USD"},
    {"ticker": "IEMG",   "name": "iShares Core MSCI Emerging Mkts", "shares": 400,  "cost_price": 48.00,  "asset_class": "ETF",      "sector": "Emerging Markets",        "currency": "USD"},
    {"ticker": "AGG",    "name": "iShares Core US Aggregate Bond",  "shares": 300,  "cost_price": 96.00,  "asset_class": "Bond ETF", "sector": "Fixed Income",            "currency": "USD"},
]

# Supported reporting currencies
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF"]

# FX ticker map: to convert CCY → USD (base)
# Format: "CYYUSD=X" gives units of USD per 1 unit of CCY
FX_PAIRS = {
    "EUR": "EURUSD=X",
    "GBP": "GBPUSD=X",
    "JPY": "JPYUSD=X",
    "CHF": "CHFUSD=X",
    "USD": None,   # base, no conversion needed
}
