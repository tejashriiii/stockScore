import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
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

        with st.spinner('Fetching scoring metrics...'):
            metrics = get_data(stock_symbol=query + '.NS')

        if metrics is None:
            st.error(f"Could not fetch scoring data for '{query}'. Check the ticker symbol or try again in a moment.")
            st.stop()

        score = calculate_stock_score(metrics=metrics)
        st.header(f"Overall score of {query} is: {round(score, 2)}")
        st.write(' NOTE: A score greater than or equal to 0.5 indicates a favorable buying opportunity 📈')
        st.write(' NOTE: A score less than 0.5 indicates a favorable selling opportunity 📉')

        with st.spinner('Generating AI analysis...'):
            explanation = get_ai_explanation(query, score, fundamental_details, metrics)

        st.subheader("AI Analysis")
        st.write(explanation)

