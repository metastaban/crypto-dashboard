# Cryptocurrency Dashboard

A real-time cryptocurrency tracking dashboard built with Streamlit and CryptoCompare API. Monitor cryptocurrency prices, market statistics, and trends with a modern, responsive interface.

## Features

- Real-time cryptocurrency price tracking
- 24-hour market statistics
- Multiple currency support
- Responsive design for all devices
- Modern, dark-themed UI
- Dynamic price change indicators
- Market cap and volume tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/metastaban/crypto-dashboard.git
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

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

## Dependencies

- Python 3.8+
- Streamlit 1.29.0
- Pandas 2.1.4
- Plotly 5.18.0
- CryptoCompare 0.7.6
- NumPy 1.26.2

## Data Source

This dashboard uses the [CryptoCompare API](https://min-api.cryptocompare.com/) for real-time cryptocurrency data.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing framework
- [CryptoCompare](https://www.cryptocompare.com/) for the cryptocurrency data API
- [Plotly](https://plotly.com/) for interactive charts
