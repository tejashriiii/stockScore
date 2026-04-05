import yfinance as yf
import pandas as pd
import numpy as np
import time


def calculate_fundamental_score(ticker):
    stock = yf.Ticker(ticker + '.NS')

    for attempt in range(3):
        try:
            balance_sheet = stock.balance_sheet
            financials = stock.financials
            cashflow = stock.cashflow
            info = stock.info
            break
        except Exception as e:
            if attempt < 2:
                print(f"Rate limited, retrying in 10s... (attempt {attempt+1})")
                time.sleep(10)
            else:
                print(f"Rate limited after 3 attempts: {e}")
                return None

    if balance_sheet.empty or financials.empty or cashflow.empty:
        print(f"Data not available for {ticker}.")
        return None

    try:
        roe = financials.loc['Net Income'].iloc[0] / balance_sheet.loc['Stockholders Equity'].iloc[0]
        net_profit_margin = financials.loc['Net Income'].iloc[0] / financials.loc['Total Revenue'].iloc[0]
        pe_ratio = info.get("trailingPE", np.nan)
        pb_ratio = info.get("priceToBook", np.nan)
        debt_to_equity = balance_sheet.loc['Current Liabilities'].iloc[0] / balance_sheet.loc['Stockholders Equity'].iloc[0]
        roa = financials.loc['Net Income'].iloc[0] / balance_sheet.loc['Total Assets'].iloc[0]
        asset_turnover = financials.loc['Total Revenue'].iloc[0] / balance_sheet.loc['Total Assets'].iloc[0]
        revenue_growth = (financials.loc['Total Revenue'].iloc[0] - financials.loc['Total Revenue'].iloc[1]) / financials.loc['Total Revenue'].iloc[1]
        net_income_growth = (financials.loc['Net Income'].iloc[0] - financials.loc['Net Income'].iloc[1]) / financials.loc['Net Income'].iloc[1]
    except KeyError as e:
        print(f"Missing data for calculation: {e}")
        return None

    scores = {
        'ROE': 1 if roe > 0.15 else 0,
        'Net Profit Margin': 1 if net_profit_margin > 0.1 else 0,
        'P/E Ratio': 1 if pe_ratio < 20 else 0,
        'P/B Ratio': 1 if pb_ratio < 3 else 0,
        'Debt-to-Equity': 1 if debt_to_equity < 1 else 0,
        'ROA': 1 if roa > 0.05 else 0,
        'Asset Turnover': 1 if asset_turnover > 0.5 else 0,
        'Revenue Growth': 1 if revenue_growth > 0.05 else 0,
        'Net Income Growth': 1 if net_income_growth > 0.05 else 0
    }

    return {metric: '✅' if score else '❌' for metric, score in scores.items()}