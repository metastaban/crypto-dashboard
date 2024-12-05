# Cryptocurrency Dashboard

A real-time cryptocurrency tracking dashboard built with Streamlit and Binance API. Track your favorite cryptocurrencies, view technical indicators, and analyze market trends with a modern, dark-themed interface.

## Features

- Real-time cryptocurrency price tracking
- Multi-currency support (USD, EUR, GBP, JPY, TRY, BTC)
- Technical indicators (RSI, MACD)
- Candlestick charts with volume analysis
- Modern dark theme interface
- Responsive design

## Installation

1. Clone the repository:
```bash
git clone [your-repo-url]
cd financial_dashboard
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Use the sidebar to:
   - Select your cryptocurrency
   - Choose your preferred currency
   - Set time intervals
   - Select date range

## Technologies Used

- [Streamlit](https://streamlit.io/) - Web interface
- [Python-Binance](https://python-binance.readthedocs.io/) - Binance API wrapper
- [Plotly](https://plotly.com/) - Interactive charts
- [Pandas](https://pandas.pydata.org/) - Data manipulation

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
