import streamlit as st
import time
from src.fundamental_score import calculate_fundamental_score
from src.scores import calculate_stock_score
from src.get_data_for_scoring_yfinance import get_data

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