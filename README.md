# Stock Scoring System

A rule and weight-based system for evaluating NSE-listed stocks based on fundamental, technical, risk, and market parameters. The system assigns a score between 0 and 1, and uses Google Gemini AI to generate an analysis of the result.

- **Score >= 0.5** — Favorable buying opportunity
- **Score < 0.5** — Favorable selling/short opportunity


## UI Preview

<img width="1470" height="733" alt="image" src="https://github.com/user-attachments/assets/cba735ce-066f-431f-8bff-adaf5440c2a3" />
<img width="1453" height="419" alt="image" src="https://github.com/user-attachments/assets/5efc46e0-2b44-46ef-847f-64769943b20f" />



## How It Works

1. Enter an NSE stock symbol (e.g. RELIANCE, INFY, TCS) and click **Get Score**.
2. The system fetches live data from Yahoo Finance via `yfinance`.
3. Fundamental ratios are evaluated and displayed as pass/fail indicators.
4. A weighted score is computed across four categories and displayed with a buy/sell recommendation.
5. Google Gemini AI analyses the score and metrics and generates a plain English investment summary.


## Scoring Methodology

| Category | Weight |
|---|---|
| Fundamental Analysis | 40% |
| Technical Indicators | 30% |
| Risk Factors | 20% |
| Other Factors | 10% |

The final score is a weighted sum across ~30 metrics, including P/E ratio, ROE, MACD, RSI, Bollinger Bands, Beta, ATR, and more.


## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/tejashriiii/stockScore.git
cd stockScore
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up your Gemini API key

Get a free API key from [aistudio.google.com](https://aistudio.google.com), then create a `.env` file in the project root:

```
GEMINI_API_KEY="your-key-here"
```

The `.env` file is git-ignored and will never be pushed to GitHub.

### 4. Run the application

```bash
streamlit run main.py
```





## Usage Notes

- This app only supports **NSE-listed Indian stocks**. Tickers are automatically suffixed with `.NS` for Yahoo Finance.
- If a fetch fails on the first attempt, the app will automatically retry up to 3 times before showing an error.
- Yahoo Finance is an unofficial data source. Occasional rate limiting or data gaps are expected.
- The Gemini free tier allows 15 requests per minute. If you hit a quota error, wait a moment and try again.


---

## Technologies Used

- **Python** — data processing and scoring logic
- **Streamlit** — web UI
- **yfinance** — live stock data from Yahoo Finance
- **Pandas, NumPy** — data handling
- **Plotly** — charting
- **Google Gemini AI** — investment analysis





## Future Improvements

- Agentic AI and RAG integration for natural language stock analysis
- Support for BSE-listed stocks and international markets




## Original Author

This project was originally created by [Shubham Mandowara](https://github.com/ShubhamMandowara). Bug fixes and AI integration by contributor.




## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Open an issue or submit a pull request to suggest improvements.
