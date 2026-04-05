import time
import yfinance as yf
import pandas as pd
from indicators.stochastic_rsi import stochastic_rsi
from indicators.macd import macd
from indicators.bollinger_bands import bollinger_bands
from indicators.average_directional_index import average_directional_index
from indicators.ma import ma
from indicators.stochastic_oscillator import stochastic_fast


def calculate_growth_rate(current, previous):
    if current and previous:
        return ((current - previous) / previous) * 100
    return None


def get_beta(stock_symbol, market_symbol='^NSEI', period='1y'):
    stock = yf.Ticker(stock_symbol)
    market = yf.Ticker(market_symbol)

    stock_data = stock.history(period=period)
    market_data = market.history(period=period)

    stock_data['Return'] = stock_data['Close'].pct_change()
    market_data['Return'] = market_data['Close'].pct_change()

    data = pd.merge(stock_data[['Return']], market_data[['Return']], left_index=True, right_index=True, suffixes=('_stock', '_market'))
    data = data.dropna()

    covariance = data['Return_stock'].cov(data['Return_market'])
    market_variance = data['Return_market'].var()
    beta = covariance / market_variance
    return beta


def get_atr(stock_symbol, period=14):
    stock = yf.Ticker(stock_symbol)
    data = stock.history(period="1y")

    data['High-Low'] = data['High'] - data['Low']
    data['High-Close'] = (data['High'] - data['Close'].shift()).abs()
    data['Low-Close'] = (data['Low'] - data['Close'].shift()).abs()
    data['True Range'] = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
    data['ATR'] = data['True Range'].rolling(window=period).mean()

    latest_atr = data['ATR'].iloc[-1]
    current_price = data['Close'].iloc[-1]
    atr_percentage = (latest_atr / current_price) * 100
    return atr_percentage


def get_data(stock_symbol):
    stock = yf.Ticker(stock_symbol)

    for attempt in range(3):
        try:
            info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            history = stock.history(period="1y")
            break
        except Exception as e:
            if attempt < 2:
                print(f"Rate limited, retrying in 10s... (attempt {attempt+1})")
                time.sleep(10)
            else:
                print(f"Failed after 3 attempts: {e}")
                return None

    metrics = {}

    if info.get("trailingPE") is not None:
        metrics["P/E Ratio"] = info.get("trailingPE")
    if info.get("priceToBook") is not None:
        metrics["P/B Ratio"] = info.get("priceToBook")
    if info.get("PegRatio") is not None:
        metrics["PEG Ratio"] = info.get("PegRatio")
    if info.get("debtToEquity") is not None:
        metrics["D/E Ratio"] = info.get("debtToEquity")

    if info.get("returnOnEquity") is not None:
        metrics["ROE (%)"] = info.get("returnOnEquity") * 100
    if info.get("profitMargins") is not None:
        metrics["Net Profit Margin (%)"] = info.get("profitMargins") * 100
    if info.get("operatingMargins") is not None:
        metrics["Operating Margin (%)"] = info.get("operatingMargins") * 100
    if info.get("grossMargins") is not None:
        metrics["Gross Margin (%)"] = info.get("grossMargins") * 100

    revenue_growth = calculate_growth_rate(
        financials.loc["Total Revenue"].iloc[0],
        financials.loc["Total Revenue"].iloc[1] if len(financials.loc["Total Revenue"]) > 1 else 0
    )
    metrics["Revenue Growth (%)"] = revenue_growth

    free_cash_flow = cashflow.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cashflow.index else 0
    fcf_growth = calculate_growth_rate(
        free_cash_flow,
        cashflow.loc["Operating Cash Flow"].iloc[1] if len(cashflow.loc["Operating Cash Flow"]) > 1 else 0
    )
    metrics["FCF Growth (%)"] = fcf_growth

    metrics["EPS Growth (%)"] = info.get("earningsGrowth") * 100 if info.get("earningsGrowth") is not None else 0

    new_financials = stock.quarterly_financials.T
    if 'Net Income' not in new_financials.columns:
        print("Net Income data not available.")
        return None

    net_income = new_financials['Net Income']
    if len(net_income) < 2:
        print("Insufficient data to calculate YoY Profit Growth.")
        return None

    current_year_profit = net_income.iloc[0]
    previous_year_profit = net_income.iloc[1]
    yoy_profit_growth = ((current_year_profit - previous_year_profit) / previous_year_profit) * 100
    metrics['YoY Profit Growth (%)'] = yoy_profit_growth

    if 'Total Revenue' not in new_financials.columns:
        print("Total Revenue data not available.")
        return None

    revenue = new_financials['Total Revenue']
    if len(revenue) < 2:
        print("Insufficient data to calculate YoY Sales Growth.")
        return None

    yoy_sales_growth = ((revenue.iloc[0] - revenue.iloc[1]) / revenue.iloc[1]) * 100
    metrics['YoY Sales Growth (%)'] = yoy_sales_growth

    qoq_sales_growth = ((revenue.iloc[0] - revenue.iloc[1]) / revenue.iloc[1]) * 100
    metrics['QoQ Sales Growth (%)'] = qoq_sales_growth

    qoq_profit_growth = ((net_income.iloc[0] - net_income.iloc[1]) / net_income.iloc[1]) * 100
    metrics['QoQ Profit Growth (%)'] = qoq_profit_growth

    if info.get("currentRatio") is not None:
        metrics["Current Ratio"] = info.get("currentRatio")

    required_fields = ["Inventory", "Accounts Receivable", "Accounts Payable"]
    for field in required_fields:
        if field not in balance_sheet.index:
            print(f"Missing {field} in balance sheet, skipping CCC calculation.")
            metrics['Cash Conversion cycle (Days)'] = 0
            break
    else:
        if "Cost Of Revenue" not in financials.index or "Total Revenue" not in financials.index:
            metrics['Cash Conversion cycle (Days)'] = 0
        else:
            inventory = balance_sheet.loc["Inventory"].mean()
            accounts_receivable = balance_sheet.loc["Accounts Receivable"].mean()
            accounts_payable = balance_sheet.loc["Accounts Payable"].mean()
            cogs = financials.loc["Cost Of Revenue"].mean()
            revenue_mean = financials.loc["Total Revenue"].mean()
            dio = (inventory / cogs) * 365 if cogs else 0
            dso = (accounts_receivable / revenue_mean) * 365 if revenue_mean else 0
            dpo = (accounts_payable / cogs) * 365 if cogs else 0
            metrics['Cash Conversion cycle (Days)'] = float(dio + dso - dpo)

    ebit = financials.loc["EBIT"].iloc[0] if "EBIT" in financials.index else 0
    interest_expense = financials.loc["Interest Expense"].iloc[0] if "Interest Expense" in financials.index else 0
    metrics["Interest Coverage Ratio"] = ebit / abs(interest_expense) if ebit and interest_expense else 0

    atr_percentage = get_atr(stock_symbol)
    metrics["Volatility (ATR %)"] = float(atr_percentage)

    metrics['Beta'] = float(get_beta(stock_symbol=stock_symbol))
    history = stochastic_rsi(df=history)
    history = macd(df=history)
    history = bollinger_bands(df=history)
    history = average_directional_index(df=history)
    history = ma(df=history, period=50)
    history = stochastic_fast(df=history)
    history = ma(df=history, period=200)
    history['Volatility (%)'] = ((history['High'] - history['Low']) / history['Close']) * 100
    metrics['Volatility (%)'] = float(history['Volatility (%)'].mean())

    metrics['Promoter Holding'] = info.get("heldPercentInsiders", "N/A")
    metrics['Institutions Holding'] = info.get("heldPercentInstitutions", "N/A")
    metrics['RSI'] = round(float(history['RSI'].iloc[-1]), 2)
    metrics['MACD Signal Line Cross'] = round(float(history['MACD_HIST'].iloc[-1]), 2)
    metrics['Volume Change (%)'] = float(round((history['Volume'].iloc[-1] - history['Volume'].iloc[-2]) / history['Volume'].iloc[-2], 2))
    metrics['Price Above SMA-200 (%)'] = float(round((history['Close'].iloc[-1] - history['MA_200'].iloc[-1]) / history['MA_200'].iloc[-1], 2))
    metrics['Stochastic Oscillator'] = round(float(history['STOCH_FAST_D'].iloc[-1]), 2)
    metrics['SMA-50 vs SMA-200'] = float(round((history['MA_50'].iloc[-1] - history['MA_200'].iloc[-1]) / history['MA_200'].iloc[-1], 2))
    metrics['Price Change (%)'] = float(round((history['Close'].iloc[-1] - history['Close'].iloc[-2]) / history['Close'].iloc[-2], 2))
    metrics['Bollinger Bands %B'] = float(round((history['BB_UPPER'].iloc[-1] - history['BB_LOWER'].iloc[-1]) / history['BB_LOWER'].iloc[-1], 2))

    market_price = info.get("currentPrice")
    price_52_week_high = history["High"].max()
    price_52_week_low = history["Low"].min()
    metrics['Price Moved from 52-Week High (%)'] = float(((market_price - price_52_week_high) / price_52_week_high) * 100)
    metrics["Price (₹)"] = market_price
    metrics['Market Cap (₹)'] = info.get('marketCap') if info.get("marketCap") else 0
    metrics['Price Away from 52-Week Low (%)'] = float(((market_price - price_52_week_low) / price_52_week_low) * 100)
    metrics['PEG Ratio'] = info.get('trailingPegRatio') if info.get("trailingPegRatio") is not None else 0
    metrics['MACD Signal'] = float(history['MACD_SIGN'].iloc[-1])
    metrics["Dividend Yield (%)"] = info.get("dividendYield") * 100 if info.get("dividendYield") else 0

    return metrics