# nav_engine.py
# Core Fund Accounting Logic — NAV Calculation Engine (with FX support)

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from portfolio import PORTFOLIO, FX_PAIRS

STALE_THRESHOLD_MINUTES = 30


def fetch_fx_rates(reporting_ccy: str = "USD") -> dict:
    """
    Fetch FX rates for all currencies in portfolio.
    All rates are expressed as: 1 unit of local CCY = X units of reporting CCY.

    Returns dict: { "EUR": 1.08, "GBP": 1.27, "USD": 1.0, ... }
    """
    # Collect unique currencies needed
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
            ticker = yf.Ticker(pair)
            rate = ticker.fast_info.last_price
            if rate and not np.isnan(rate):
                rates_in_usd[ccy] = round(float(rate), 6)
            else:
                # fallback: try history
                hist = ticker.history(period="2d")
                if not hist.empty:
                    rates_in_usd[ccy] = round(float(hist["Close"].iloc[-1]), 6)
                else:
                    rates_in_usd[ccy] = None
        except Exception:
            rates_in_usd[ccy] = None

    # Now convert: 1 local CCY → reporting CCY
    # rates_in_usd[ccy] = USD per 1 local CCY
    # rates_in_usd[reporting_ccy] = USD per 1 reporting CCY
    # => local→reporting = rates_in_usd[local] / rates_in_usd[reporting]

    reporting_usd_rate = rates_in_usd.get(reporting_ccy, 1.0) or 1.0
    fx_rates = {}
    for ccy, usd_rate in rates_in_usd.items():
        if usd_rate is None:
            fx_rates[ccy] = {"rate": None, "stale": True}
        else:
            fx_rates[ccy] = {
                "rate": round(usd_rate / reporting_usd_rate, 6),
                "stale": False,
            }

    # reporting CCY to itself is always 1.0
    fx_rates[reporting_ccy] = {"rate": 1.0, "stale": False}
    return fx_rates


def fetch_prices(tickers: list[str]) -> dict:
    """
    Fetch latest prices from Yahoo Finance.
    Returns dict: { ticker: { price, prev_close, timestamp, stale, missing } }
    """
    results = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker)
            info = data.fast_info
            price = info.last_price
            prev_close = info.previous_close

            stale = False
            if price is None or np.isnan(price):
                stale = True
                missing = True
                price = prev_close
            else:
                missing = False

            results[ticker] = {
                "price":      round(float(price), 4) if price else None,
                "prev_close": round(float(prev_close), 4) if prev_close else None,
                "stale":      stale,
                "missing":    missing,
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
            }
        except Exception as e:
            results[ticker] = {
                "price": None, "prev_close": None,
                "stale": True, "missing": True,
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
                "error": str(e),
            }
    return results


def calculate_nav(price_data: dict, reporting_ccy: str = "USD", fx_rates: dict = None) -> pd.DataFrame:
    """
    Calculate NAV, P&L, unrealised gains/losses for each holding.
    Supports multi-currency portfolios — all values converted to reporting_ccy.
    """
    if fx_rates is None:
        fx_rates = {ccy: {"rate": 1.0, "stale": False} for ccy in ["USD", "EUR", "GBP"]}

    rows = []
    for holding in PORTFOLIO:
        ticker = holding["ticker"]
        px = price_data.get(ticker, {})
        local_ccy = holding.get("currency", "USD")

        current_price = px.get("price")
        prev_close    = px.get("prev_close")
        cost_price    = holding["cost_price"]
        shares        = holding["shares"]

        fx_info  = fx_rates.get(local_ccy, {"rate": 1.0, "stale": False})
        fx_rate  = fx_info.get("rate") or 1.0
        fx_stale = fx_info.get("stale", False)

        # Local currency values
        local_mv         = round(current_price * shares, 2) if current_price else None
        local_cost_basis = round(cost_price * shares, 2)

        # Reporting currency values
        market_value = round(local_mv * fx_rate, 2)         if local_mv is not None else None
        cost_basis   = round(local_cost_basis * fx_rate, 2)

        unrealised_pnl = round(market_value - cost_basis, 2) if market_value is not None else None
        unrealised_pct = round((unrealised_pnl / cost_basis) * 100, 2) if unrealised_pnl is not None and cost_basis else None

        daily_pnl = None
        daily_pct = None
        if current_price and prev_close:
            daily_pnl = round((current_price - prev_close) * shares * fx_rate, 2)
            daily_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

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
            "Price As At":     px.get("fetched_at", "—"),
        })

    df = pd.DataFrame(rows)
    total_mv = df["Market Value"].sum()
    df["Weight %"] = df["Market Value"].apply(
        lambda mv: round((mv / total_mv) * 100, 2) if total_mv and mv else None
    )
    return df


def get_fund_summary(df: pd.DataFrame, reporting_ccy: str = "USD") -> dict:
    """Roll up to fund-level NAV summary."""
    total_market_value  = df["Market Value"].sum()
    total_cost_basis    = df["Cost Basis"].sum()
    total_unrealised    = df["Unrealised P&L"].sum()
    total_daily_pnl     = df["Daily P&L"].sum()
    total_unrealised_pct = round((total_unrealised / total_cost_basis) * 100, 2) if total_cost_basis else 0

    stale_count   = df["Stale Price"].sum()
    missing_count = df["Missing Price"].sum()
    fx_stale      = df["FX Stale"].sum()

    # Currency exposure
    ccy_exposure = (
        df.groupby("Currency")["Market Value"]
        .sum()
        .apply(lambda v: round((v / total_market_value) * 100, 2) if total_market_value else 0)
        .to_dict()
    )

    return {
        "nav":               round(total_market_value, 2),
        "cost_basis":        round(total_cost_basis, 2),
        "unrealised_pnl":    round(total_unrealised, 2),
        "unrealised_pct":    total_unrealised_pct,
        "daily_pnl":         round(total_daily_pnl, 2),
        "num_holdings":      len(df),
        "stale_prices":      int(stale_count),
        "missing_prices":    int(missing_count),
        "fx_stale":          int(fx_stale),
        "pricing_alerts":    int(stale_count + missing_count),
        "ccy_exposure":      ccy_exposure,
        "reporting_ccy":     reporting_ccy,
        "last_calculated":   datetime.now().strftime("%d %b %Y %H:%M:%S"),
    }
