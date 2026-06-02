# nav_engine.py
# Core Fund Accounting Logic — NAV Calculation Engine (with FX support)

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from portfolio import PORTFOLIO, FX_PAIRS

STALE_THRESHOLD_MINUTES = 30

# Tickers that trade in pence on LSE — divide price by 100 to get GBP
LSE_PENCE_TICKERS = {"SHEL.L", "AZN.L", "HSBA.L", "RIO.L", "ULVR.L", "BP.L", "GSK.L", "BATS.L"}

# Fallback tickers when primary fails (e.g. Swiss/EU tickers → US ADR)
TICKER_FALLBACKS = {
    "ROG.SW":  "RHHBY",   # Roche → US OTC ADR
    "NESN.SW": "NSRGY",   # Nestlé → US OTC ADR
    "NOVN.SW": "NVS",     # Novartis → NYSE ADR
    "SIE.DE":  "SIEGY",   # Siemens → US OTC ADR
    "AIR.PA":  "EADSY",   # Airbus → US OTC ADR
    "MC.PA":   "LVMUY",   # LVMH → US OTC ADR
    "OR.PA":   "LRLCY",   # L'Oréal → US OTC ADR
    "7203.T":  "TM",      # Toyota → NYSE ADR
    "6758.T":  "SONY",    # Sony → NYSE ADR
    "9984.T":  "SFTBY",   # SoftBank → US OTC ADR
}


def _fetch_single(ticker: str) -> dict:
    """
    Fetch price for a single ticker with history fallback.
    Never raises — always returns a dict.
    """
    def _try_ticker(t: str):
        data  = yf.Ticker(t)
        info  = data.fast_info
        price = info.last_price
        prev  = info.previous_close

        # If fast_info fails, try history
        if price is None or (isinstance(price, float) and np.isnan(price)):
            hist = data.history(period="5d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                prev  = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
            else:
                price, prev = None, None

        return price, prev

    fetched_at = datetime.now().strftime("%H:%M:%S")

    # ── Primary attempt ───────────────────────────────────────────────────────
    price, prev = None, None
    used_fallback = False
    try:
        price, prev = _try_ticker(ticker)
    except Exception:
        pass

    # ── Fallback ticker ───────────────────────────────────────────────────────
    if (price is None) and ticker in TICKER_FALLBACKS:
        fallback = TICKER_FALLBACKS[ticker]
        try:
            price, prev = _try_ticker(fallback)
            used_fallback = True
        except Exception:
            pass

    # ── LSE pence → GBP conversion ────────────────────────────────────────────
    if ticker in LSE_PENCE_TICKERS and price and price > 500:
        price = price / 100
        prev  = prev / 100 if prev else None

    stale   = price is None
    missing = price is None

    return {
        "price":         round(float(price), 4) if price is not None else None,
        "prev_close":    round(float(prev),  4) if prev  is not None else None,
        "stale":         stale,
        "missing":       missing,
        "used_fallback": used_fallback,
        "fetched_at":    fetched_at,
    }


def fetch_prices(tickers: list[str]) -> dict:
    """
    Fetch latest prices for all tickers.
    Guarantees every ticker has an entry — never silently drops one.
    """
    results = {}
    for ticker in tickers:
        results[ticker] = _fetch_single(ticker)
    return results


def fetch_fx_rates(reporting_ccy: str = "USD") -> dict:
    """
    Fetch FX rates for all portfolio currencies.
    Returns: { "EUR": {"rate": 1.08, "stale": False}, ... }
    All rates expressed as: 1 local CCY = X reporting CCY.
    """
    portfolio_ccys = set(h.get("currency", "USD") for h in PORTFOLIO)
    all_ccys = portfolio_ccys | {reporting_ccy}

    rates_in_usd = {"USD": 1.0}

    for ccy in all_ccys:
        if ccy == "USD":
            continue
        pair = FX_PAIRS.get(ccy)
        if not pair:
            rates_in_usd[ccy] = 1.0
            continue
        try:
            t    = yf.Ticker(pair)
            rate = t.fast_info.last_price
            if rate is None or (isinstance(rate, float) and np.isnan(rate)):
                hist = t.history(period="2d")
                rate = float(hist["Close"].iloc[-1]) if not hist.empty else None
            rates_in_usd[ccy] = round(float(rate), 6) if rate else None
        except Exception:
            rates_in_usd[ccy] = None

    reporting_usd_rate = rates_in_usd.get(reporting_ccy, 1.0) or 1.0
    fx_rates = {}
    for ccy, usd_rate in rates_in_usd.items():
        if usd_rate is None:
            fx_rates[ccy] = {"rate": None, "stale": True}
        else:
            fx_rates[ccy] = {
                "rate":  round(usd_rate / reporting_usd_rate, 6),
                "stale": False,
            }

    fx_rates[reporting_ccy] = {"rate": 1.0, "stale": False}
    return fx_rates


def calculate_nav(price_data: dict, reporting_ccy: str = "USD", fx_rates: dict = None) -> pd.DataFrame:
    """
    Calculate NAV, P&L, unrealised gains/losses for each holding.
    All holdings always appear — missing prices show as stale/missing flags.
    """
    if fx_rates is None:
        fx_rates = {ccy: {"rate": 1.0, "stale": False} for ccy in ["USD", "EUR", "GBP", "JPY", "CHF"]}

    rows = []
    for holding in PORTFOLIO:
        ticker    = holding["ticker"]
        px        = price_data.get(ticker, {"price": None, "prev_close": None, "stale": True, "missing": True, "fetched_at": "—"})
        local_ccy = holding.get("currency", "USD")

        current_price = px.get("price")
        prev_close    = px.get("prev_close")
        cost_price    = holding["cost_price"]
        shares        = holding["shares"]

        fx_info  = fx_rates.get(local_ccy, {"rate": 1.0, "stale": False})
        fx_rate  = fx_info.get("rate") or 1.0
        fx_stale = fx_info.get("stale", False)

        local_mv         = round(current_price * shares, 2) if current_price is not None else None
        local_cost_basis = round(cost_price * shares, 2)
        market_value     = round(local_mv * fx_rate, 2)     if local_mv is not None else None
        cost_basis       = round(local_cost_basis * fx_rate, 2)

        unrealised_pnl = round(market_value - cost_basis, 2)             if market_value is not None else None
        unrealised_pct = round((unrealised_pnl / cost_basis) * 100, 2)   if unrealised_pnl is not None and cost_basis else None

        daily_pnl, daily_pct = None, None
        if current_price is not None and prev_close is not None:
            daily_pnl = round((current_price - prev_close) * shares * fx_rate, 2)
            daily_pct = round(((current_price - prev_close) / prev_close) * 100, 2) if prev_close != 0 else None

        rows.append({
            "Ticker":          ticker,
            "Name":            holding["name"],
            "Asset Class":     holding["asset_class"],
            "Sector":          holding["sector"],
            "Currency":        local_ccy,
            "FX Rate":         fx_rate,
            "FX Stale":        fx_stale,
            "Shares":          shares,
            "Cost Price":      cost_price,
            "Current Price":   current_price,
            "Local MV":        local_mv,
            "Cost Basis":      cost_basis,
            "Market Value":    market_value,
            "Unrealised P&L":  unrealised_pnl,
            "Unrealised %":    unrealised_pct,
            "Daily P&L":       daily_pnl,
            "Daily %":         daily_pct,
            "Stale Price":     px.get("stale", False),
            "Missing Price":   px.get("missing", False),
            "Used Fallback":   px.get("used_fallback", False),
            "Price As At":     px.get("fetched_at", "—"),
        })

    df = pd.DataFrame(rows)
    total_mv = df["Market Value"].sum()
    df["Weight %"] = df["Market Value"].apply(
        lambda mv: round((mv / total_mv) * 100, 2) if total_mv and mv is not None else None
    )
    return df


def get_fund_summary(df: pd.DataFrame, reporting_ccy: str = "USD") -> dict:
    """Roll up to fund-level NAV summary."""
    total_market_value   = df["Market Value"].sum()
    total_cost_basis     = df["Cost Basis"].sum()
    total_unrealised     = df["Unrealised P&L"].sum()
    total_daily_pnl      = df["Daily P&L"].sum()
    total_unrealised_pct = round((total_unrealised / total_cost_basis) * 100, 2) if total_cost_basis else 0

    stale_count   = df["Stale Price"].sum()
    missing_count = df["Missing Price"].sum()
    fx_stale      = df["FX Stale"].sum()

    ccy_exposure = (
        df.groupby("Currency")["Market Value"]
        .sum()
        .apply(lambda v: round((v / total_market_value) * 100, 2) if total_market_value else 0)
        .to_dict()
    )

    return {
        "nav":             round(total_market_value, 2),
        "cost_basis":      round(total_cost_basis, 2),
        "unrealised_pnl":  round(total_unrealised, 2),
        "unrealised_pct":  total_unrealised_pct,
        "daily_pnl":       round(total_daily_pnl, 2),
        "num_holdings":    len(df),
        "stale_prices":    int(stale_count),
        "missing_prices":  int(missing_count),
        "fx_stale":        int(fx_stale),
        "pricing_alerts":  int(stale_count + missing_count),
        "ccy_exposure":    ccy_exposure,
        "reporting_ccy":   reporting_ccy,
        "last_calculated": datetime.now().strftime("%d %b %Y %H:%M:%S"),
    }
