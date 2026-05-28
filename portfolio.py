# portfolio.py
# Mock Fund Portfolio — Mix of EMPOWER Top Holdings + Global ETFs

FUND_NAME = "NAV Dashboard"

PORTFOLIO = [
    # --- EMPOWER Top Share Holdings ---
    {"ticker": "NVDA",  "name": "NVIDIA Corp",                     "shares": 150,   "cost_price": 80.00,  "asset_class": "Equity", "sector": "Information Technology"},
    {"ticker": "AAPL",  "name": "Apple Inc",                       "shares": 200,   "cost_price": 150.00, "asset_class": "Equity", "sector": "Information Technology"},
    {"ticker": "GOOGL", "name": "Alphabet Inc",                    "shares": 180,   "cost_price": 120.00, "asset_class": "Equity", "sector": "Communication Services"},
    {"ticker": "MSFT",  "name": "Microsoft Corp",                  "shares": 120,   "cost_price": 280.00, "asset_class": "Equity", "sector": "Information Technology"},
    {"ticker": "AMZN",  "name": "Amazon.com Inc",                  "shares": 130,   "cost_price": 130.00, "asset_class": "Equity", "sector": "Consumer Discretionary"},
    {"ticker": "TSM",   "name": "Taiwan Semiconductor",            "shares": 200,   "cost_price": 90.00,  "asset_class": "Equity", "sector": "Information Technology"},
    {"ticker": "AVGO",  "name": "Broadcom Inc",                    "shares": 80,    "cost_price": 550.00, "asset_class": "Equity", "sector": "Information Technology"},
    {"ticker": "TSLA",  "name": "Tesla Inc",                       "shares": 160,   "cost_price": 200.00, "asset_class": "Equity", "sector": "Consumer Discretionary"},
    {"ticker": "META",  "name": "Meta Platforms Inc",              "shares": 100,   "cost_price": 250.00, "asset_class": "Equity", "sector": "Communication Services"},
    {"ticker": "ASML",  "name": "ASML Holding NV",                 "shares": 40,    "cost_price": 600.00, "asset_class": "Equity", "sector": "Information Technology"},

    # --- Global ETFs ---
    {"ticker": "VWRL.L","name": "Vanguard FTSE All-World ETF",     "shares": 500,   "cost_price": 95.00,  "asset_class": "ETF",    "sector": "Global Equity"},
    {"ticker": "SPY",   "name": "SPDR S&P 500 ETF",                "shares": 300,   "cost_price": 420.00, "asset_class": "ETF",    "sector": "US Equity"},
    {"ticker": "QQQ",   "name": "Invesco QQQ (Nasdaq 100)",        "shares": 150,   "cost_price": 350.00, "asset_class": "ETF",    "sector": "US Tech Equity"},
    {"ticker": "IEMG",  "name": "iShares Core MSCI Emerging Mkts", "shares": 400,   "cost_price": 48.00,  "asset_class": "ETF",    "sector": "Emerging Markets"},
    {"ticker": "AGG",   "name": "iShares Core US Aggregate Bond",  "shares": 300,   "cost_price": 96.00,  "asset_class": "Bond ETF","sector": "Fixed Income"},
]
