import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import plotly.graph_objects as go
from src.fundamental_score import calculate_fundamental_score
from src.scores import calculate_stock_score
from src.get_data_for_scoring_yfinance import get_data

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_explanation(ticker, score, fundamental_details, metrics):
    model = genai.GenerativeModel("gemini-flash-lite-latest")
    prompt = f"""
You are a financial analyst. A stock scoring system has evaluated {ticker} and given it a score of {round(score, 2)} out of 1.

Fundamental indicators (pass/fail):
{fundamental_details}

Key metrics:
- P/E Ratio: {metrics.get('P/E Ratio', 'N/A')}
- ROE: {metrics.get('ROE (%)', 'N/A')}
- Debt/Equity: {metrics.get('D/E Ratio', 'N/A')}
- Revenue Growth: {metrics.get('Revenue Growth (%)', 'N/A')}
- RSI: {metrics.get('RSI', 'N/A')}
- Beta: {metrics.get('Beta', 'N/A')}
- Dividend Yield: {metrics.get('Dividend Yield (%)', 'N/A')}

Write a short 4-5 sentence analysis in plain English explaining:
1. Why the stock got this score
2. What looks good
3. What looks risky
4. A one line verdict: buy or avoid right now

Be direct and simple. No bullet points, just plain paragraphs.
"""
    response = model.generate_content(prompt)
    return response.text


def plot_fundamental_chart(fundamental_details, ticker):
    labels = list(fundamental_details.keys())
    values = [1 if v == '✅' else 0 for v in fundamental_details.values()]
    colors = ['#2ecc71' if v == 1 else '#e74c3c' for v in values]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=['Pass' if v == 1 else 'Fail' for v in values],
        textposition='outside'
    ))
    fig.update_layout(
        title=f'Fundamental Health Check — {ticker}',
        yaxis=dict(tickvals=[0, 1], ticktext=['Fail', 'Pass'], range=[-0.2, 1.5]),
        xaxis_tickangle=-30,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    return fig


def plot_key_metrics_chart(metrics, ticker):
    keys = ['P/E Ratio', 'ROE (%)', 'Net Profit Margin (%)', 'D/E Ratio',
            'RSI', 'Beta', 'Dividend Yield (%)', 'Revenue Growth (%)']
    labels = []
    values = []
    for k in keys:
        if metrics.get(k) is not None:
            labels.append(k)
            values.append(round(float(metrics[k]), 2))

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color='#3498db',
        text=values,
        textposition='outside'
    ))
    fig.update_layout(
        title=f'Key Financial Metrics — {ticker}',
        xaxis_tickangle=-30,
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    return fig


st.sidebar.title("Navigation")
menu_option = st.sidebar.selectbox("Select a section", ['Stock Score'])

if menu_option == 'Stock Score':
    st.title("Stock Score")
    query = st.text_input('Enter Stock Symbol (NSE, e.g. INFY, RELIANCE, TCS)')
    run = st.button('Get Score')

    if run and query:
        query = query.strip().upper()

        with st.spinner('Fetching fundamental details...'):
            fundamental_details = calculate_fundamental_score(ticker=query)

        st.write(f'Fundamental Details of Stock: {query}')

        if fundamental_details is None:
            st.error(f"Could not fetch fundamental data for '{query}'. Check the ticker symbol or try again in a moment.")
            st.stop()

        st.write(fundamental_details)
        st.plotly_chart(plot_fundamental_chart(fundamental_details, query), use_container_width=True)

        with st.spinner('Fetching scoring metrics...'):
            metrics = get_data(stock_symbol=query + '.NS')

        if metrics is None:
            st.error(f"Could not fetch scoring data for '{query}'. Check the ticker symbol or try again in a moment.")
            st.stop()

        st.plotly_chart(plot_key_metrics_chart(metrics, query), use_container_width=True)

        score = calculate_stock_score(metrics=metrics)
        st.header(f"Overall score of {query} is: {round(score, 2)}")
        st.write(' NOTE: A score greater than or equal to 0.5 indicates a favorable buying opportunity 📈')
        st.write(' NOTE: A score less than 0.5 indicates a favorable selling opportunity 📉')

        with st.spinner('Generating AI analysis...'):
            explanation = get_ai_explanation(query, score, fundamental_details, metrics)

        st.subheader("AI Analysis")
        st.write(explanation)