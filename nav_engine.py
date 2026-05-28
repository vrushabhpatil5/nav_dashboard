# nav_engine.py
# Core Fund Accounting Logic — NAV Calculation Engine

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from portfolio import PORTFOLIO

STALE_THRESHOLD_MINUTES = 30  # flag price as stale if older than this


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

            # Determine staleness (Yahoo doesn't give exact timestamp for free)
            # We use market hours heuristic
            now = datetime.now()
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

            stale = False
            if price is None or np.isnan(price):
                stale = True
                missing = True
                price = prev_close  # fallback to prev close
            else:
                missing = False

            results[ticker] = {
                "price": round(float(price), 4) if price else None,
                "prev_close": round(float(prev_close), 4) if prev_close else None,
                "stale": stale,
                "missing": missing,
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
            }
        except Exception as e:
            results[ticker] = {
                "price": None,
                "prev_close": None,
                "stale": True,
                "missing": True,
                "fetched_at": datetime.now().strftime("%H:%M:%S"),
                "error": str(e),
            }
    return results


def calculate_nav(price_data: dict) -> pd.DataFrame:
    """
    Calculate NAV, P&L, unrealised gains/losses for each holding.
    Returns a DataFrame with full fund accounting breakdown.
    """
    rows = []
    for holding in PORTFOLIO:
        ticker = holding["ticker"]
        px = price_data.get(ticker, {})

        current_price = px.get("price")
        prev_close = px.get("prev_close")
        cost_price = holding["cost_price"]
        shares = holding["shares"]

        # Market value
        market_value = round(current_price * shares, 2) if current_price else None

        # Cost basis
        cost_basis = round(cost_price * shares, 2)

        # Unrealised P&L
        unrealised_pnl = round(market_value - cost_basis, 2) if market_value else None
        unrealised_pct = round((unrealised_pnl / cost_basis) * 100, 2) if unrealised_pnl is not None else None

        # Daily P&L
        daily_pnl = None
        if current_price and prev_close:
            daily_pnl = round((current_price - prev_close) * shares, 2)

        # Daily return %
        daily_pct = None
        if current_price and prev_close and prev_close != 0:
            daily_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

        rows.append({
            "Ticker":           ticker,
            "Name":             holding["name"],
            "Asset Class":      holding["asset_class"],
            "Sector":           holding["sector"],
            "Shares":           shares,
            "Cost Price":       cost_price,
            "Current Price":    current_price,
            "Cost Basis":       cost_basis,
            "Market Value":     market_value,
            "Unrealised P&L":   unrealised_pnl,
            "Unrealised %":     unrealised_pct,
            "Daily P&L":        daily_pnl,
            "Daily %":          daily_pct,
            "Stale Price":      px.get("stale", False),
            "Missing Price":    px.get("missing", False),
            "Price As At":      px.get("fetched_at", "—"),
        })

    df = pd.DataFrame(rows)

    # Fund weight %
    total_mv = df["Market Value"].sum()
    df["Weight %"] = df["Market Value"].apply(
        lambda mv: round((mv / total_mv) * 100, 2) if total_mv and mv else None
    )

    return df


def get_fund_summary(df: pd.DataFrame) -> dict:
    """
    Roll up to fund-level NAV summary.
    """
    total_market_value = df["Market Value"].sum()
    total_cost_basis = df["Cost Basis"].sum()
    total_unrealised_pnl = df["Unrealised P&L"].sum()
    total_daily_pnl = df["Daily P&L"].sum()
    total_unrealised_pct = round((total_unrealised_pnl / total_cost_basis) * 100, 2) if total_cost_basis else 0

    stale_count = df["Stale Price"].sum()
    missing_count = df["Missing Price"].sum()

    return {
        "nav":                  round(total_market_value, 2),
        "cost_basis":           round(total_cost_basis, 2),
        "unrealised_pnl":       round(total_unrealised_pnl, 2),
        "unrealised_pct":       total_unrealised_pct,
        "daily_pnl":            round(total_daily_pnl, 2),
        "num_holdings":         len(df),
        "stale_prices":         int(stale_count),
        "missing_prices":       int(missing_count),
        "pricing_alerts":       int(stale_count + missing_count),
        "last_calculated":      datetime.now().strftime("%d %b %Y %H:%M:%S"),
    }
