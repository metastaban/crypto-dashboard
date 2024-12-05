import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time
import numpy as np
import requests

# Page configuration
st.set_page_config(
    page_title="Cryptocurrency Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Add custom styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 0rem;
    }
    .stApp {
        background-color: #0e1117;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Binance client
client = Client()

def get_crypto_pairs():
    """Fetches USDT pairs from Binance and prepares crypto information"""
    exchange_info = client.get_exchange_info()
    
    # Known cryptocurrency names
    crypto_names = {
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'BNB': 'Binance Coin',
        'XRP': 'Ripple',
        'ADA': 'Cardano',
        'DOGE': 'Dogecoin',
        'SOL': 'Solana',
        'DOT': 'Polkadot',
        'MATIC': 'Polygon',
        'AVAX': 'Avalanche',
        'LINK': 'Chainlink',
        'UNI': 'Uniswap',
        'ATOM': 'Cosmos',
        'LTC': 'Litecoin',
        'ETC': 'Ethereum Classic',
        'ALGO': 'Algorand',
        'XLM': 'Stellar',
        'FTM': 'Fantom',
        'NEAR': 'NEAR Protocol',
        'FIL': 'Filecoin',
        'TRX': 'TRON',
        'SHIB': 'Shiba Inu',
        'VET': 'VeChain',
        'SAND': 'The Sandbox',
        'MANA': 'Decentraland',
        'AAVE': 'Aave',
        'THETA': 'Theta Network',
        'AXS': 'Axie Infinity',
        'GRT': 'The Graph',
        'EGLD': 'Elrond'
    }

    # Get USDT pairs and create dictionary
    pairs = {}
    for symbol in exchange_info['symbols']:
        if symbol['symbol'].endswith('USDT'):
            crypto_symbol = symbol['baseAsset']  # e.g., BTC, ETH
            # Show name with symbol if listed, otherwise just symbol
            display_name = f"{crypto_symbol} - {crypto_names[crypto_symbol]}" if crypto_symbol in crypto_names else crypto_symbol
            pairs[display_name] = symbol['symbol']
    
    # Sort by names
    return dict(sorted(pairs.items()))

def get_current_price(symbol):
    """Gets current price for the selected symbol"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except BinanceAPIException as e:
        st.error(f"Error fetching data: {e}")
        return None

def get_historical_data(symbol, interval, start_date=None, end_date=None):
    """Gets historical price data"""
    try:
        # Convert dates to timestamps in milliseconds
        start_ts = int(start_date.timestamp() * 1000) if start_date else None
        end_ts = int(end_date.timestamp() * 1000) if end_date else None
        
        # Get klines/candlestick data
        klines = client.get_klines(
            symbol=symbol,
            interval=interval,
            startTime=start_ts,
            endTime=end_ts,
            limit=1000  # Maximum number of data points
        )
        
        if not klines:
            st.warning("No data available for the selected date range.")
            return None
            
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 
                                         'volume', 'close_time', 'quote_volume', 'trades', 
                                         'taker_buy_base', 'taker_buy_quote', 'ignore'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Convert string values to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df
    except BinanceAPIException as e:
        st.error(f"Error fetching data: {e}")
        return None

def get_24h_stats(symbol):
    """Gets 24-hour statistics"""
    try:
        stats = client.get_ticker(symbol=symbol)
        return {
            'price_change': float(stats['priceChange']),
            'price_change_percent': float(stats['priceChangePercent']),
            'high': float(stats['highPrice']),
            'low': float(stats['lowPrice']),
            'volume': float(stats['volume']),
            'quote_volume': float(stats['quoteVolume']),
            'count': int(stats['count']),  # Number of trades
            'weighted_avg_price': float(stats['weightedAvgPrice'])
        }
    except BinanceAPIException as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_rsi(df, periods=14):
    """Calculate RSI technical indicator"""
    close_delta = df['close'].diff()
    
    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    # Calculate the EWMA
    ma_up = up.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    ma_down = down.ewm(com=periods - 1, adjust=True, min_periods=periods).mean()
    
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD technical indicator"""
    # Calculate the MACD and signal line indicators
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram

def create_price_chart(df, currency_code="USD"):
    """Creates candlestick chart with the selected currency"""
    # Get current exchange rate
    rates = get_exchange_rates()
    rate = rates.get(currency_code, 1) if rates else 1
    
    # Convert prices to selected currency
    df_converted = df.copy()
    df_converted['open'] = df['open'] * rate
    df_converted['high'] = df['high'] * rate
    df_converted['low'] = df['low'] * rate
    df_converted['close'] = df['close'] * rate
    
    # Currency symbols for the chart title
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "TRY": "₺",
        "BTC": "₿"
    }
    currency_symbol = symbols.get(currency_code, currency_code)
    
    fig = go.Figure(data=[go.Candlestick(x=df_converted['timestamp'],
                                        open=df_converted['open'],
                                        high=df_converted['high'],
                                        low=df_converted['low'],
                                        close=df_converted['close'])])
    
    fig.update_layout(
        title=f'Price Chart ({currency_symbol})',
        yaxis_title=f'Price ({currency_code})',
        template='plotly_dark',
        height=600,
        xaxis_rangeslider_visible=False
    )
    return fig

def create_volume_chart(df):
    """Creates volume chart"""
    fig = go.Figure(data=[go.Bar(x=df['timestamp'],
                                y=df['volume'],
                                name="Volume",
                                marker_color='rgba(0,150,255,0.5)')])
    
    fig.update_layout(
        title='Volume',
        yaxis_title='Volume',
        template='plotly_dark',
        height=200,
        margin=dict(t=30, l=60, r=60, b=30)
    )
    return fig

def create_rsi_chart(df):
    """Creates RSI chart"""
    rsi = calculate_rsi(df)
    
    fig = go.Figure(data=[go.Scatter(x=df['timestamp'],
                                    y=rsi,
                                    name="RSI",
                                    line=dict(color='yellow', width=1))])
    
    # Add RSI levels
    fig.add_hline(y=70, line_width=1, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_width=1, line_dash="dash", line_color="green")
    
    fig.update_layout(
        title='RSI (14)',
        yaxis_title='RSI',
        template='plotly_dark',
        height=200,
        margin=dict(t=30, l=60, r=60, b=30)
    )
    return fig

def create_macd_chart(df):
    """Creates MACD chart"""
    macd, signal, histogram = calculate_macd(df)
    
    fig = go.Figure()
    
    # Add MACD line
    fig.add_trace(go.Scatter(x=df['timestamp'],
                            y=macd,
                            name="MACD",
                            line=dict(color='blue', width=1.5)))
    
    # Add Signal line
    fig.add_trace(go.Scatter(x=df['timestamp'],
                            y=signal,
                            name="Signal",
                            line=dict(color='orange', width=1.5)))
    
    # Add Histogram
    fig.add_trace(go.Bar(x=df['timestamp'],
                        y=histogram,
                        name="Histogram",
                        marker_color='rgba(255,255,255,0.3)'))
    
    fig.update_layout(
        title='MACD (12,26,9)',
        yaxis_title='MACD',
        template='plotly_dark',
        height=200,
        margin=dict(t=30, l=60, r=60, b=30)
    )
    return fig

def get_exchange_rates():
    """Gets current exchange rates from ExchangeRate-API"""
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        return response.json()['rates']
    except Exception as e:
        st.error(f"Error fetching exchange rates: {e}")
        return None

def convert_price(price, from_currency="USD", to_currency="USD"):
    """Converts price between currencies"""
    rates = get_exchange_rates()
    if rates and to_currency in rates:
        converted = price * rates[to_currency]
        return converted
    return price

def format_price(price, currency="USD"):
    """Formats price based on its value and currency"""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "TRY": "₺",
        "BTC": "₿"
    }
    
    symbol = symbols.get(currency, currency)
    
    if price == 0:
        return f"{symbol}0.00"
    elif price < 0.01:
        return f"{symbol}{price:.8f}"
    elif price < 1:
        return f"{symbol}{price:.6f}"
    elif price < 100:
        return f"{symbol}{price:.4f}"
    else:
        return f"{symbol}{price:,.2f}"

def create_metric_card(title, value, delta=None, prefix="", suffix=""):
    """Creates a modern metric card using HTML/CSS"""
    
    # Delta bölümü
    delta_section = ""
    if delta:
        try:
            delta_float = float(delta.replace('%', ''))
            delta_color = "#22c55e" if delta_float > 0 else "#ef4444"
            delta_arrow = "▲" if delta_float > 0 else "▼"
            delta_section = f'<span style="color: {delta_color}; margin-left: 8px; font-size: 14px;">{delta_arrow} {delta}</span>'
        except:
            pass

    html = f"""
    <div style="
        background: linear-gradient(145deg, rgba(26,26,26,0.9), rgba(32,32,32,0.9));
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.1);
    ">
        <p style="
            color: rgba(255,255,255,0.6);
            font-size: 14px;
            font-weight: 500;
            margin: 0 0 8px 0;
        ">{title}</p>
        <p style="
            color: white;
            font-size: 24px;
            font-weight: 600;
            margin: 0;
            display: flex;
            align-items: center;
        ">{prefix}{value}{suffix}{delta_section}</p>
    </div>
    """
    return st.markdown(html, unsafe_allow_html=True)

def main():
    # Custom CSS for the dashboard
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
        }
        .main {
            padding: 0;
        }
        h1 {
            color: white;
            font-size: 2.5em;
            font-weight: 600;
            margin: 0.5rem 0;
            padding-left: 1rem;
        }
        .stMetric {
            background: none !important;
            border: none !important;
        }
        .sidebar-logo {
            display: block;
            margin: 0 auto 0.5rem auto;
            width: 30%;
            padding: 0;
        }
        #MainMenu {
            visibility: hidden;
        }
        footer {
            visibility: hidden;
        }
        header {
            visibility: hidden;
        }
        .block-container {
            padding-top: 0;
            margin-top: 0;
        }
        [data-testid="stSidebarNav"] {
            padding-top: 0;
        }
        section[data-testid="stSidebar"] > div {
            padding-top: 0;
        }
        section[data-testid="stSidebar"] {
            padding-top: 0;
        }
        .stMarkdown {
            margin-top: 0;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Cryptocurrency Dashboard")
    
    # Sidebar
    with st.sidebar:
        # Logo
        st.markdown(
            '<a href="https://tastaban.net" target="_blank"><img src="https://tastaban.net/assets/logo-1SP6eNCx.png" class="sidebar-logo"></a>',
            unsafe_allow_html=True
        )
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Settings")
        
        # Cryptocurrency selection
        pairs = get_crypto_pairs()
        crypto_list = list(pairs.keys())
        # Find and set BTC as default
        default_index = 0
        for i, name in enumerate(crypto_list):
            if name.startswith('BTC -'):
                default_index = i
                break
        
        selected_crypto = st.selectbox("Select Cryptocurrency:", crypto_list, index=default_index)
        selected_symbol = pairs[selected_crypto]  # Full symbol (e.g., BTCUSDT)
        
        # Currency selection
        currencies = {
            "US Dollar": "USD",
            "Euro": "EUR",
            "British Pound": "GBP",
            "Japanese Yen": "JPY",
            "Turkish Lira": "TRY",
            "Bitcoin": "BTC"
        }
        
        selected_currency = st.selectbox(
            "Select Currency",
            list(currencies.keys()),
            index=0
        )
        currency_code = currencies[selected_currency]
        
        # Time interval selection
        intervals = {
            '1 Month': Client.KLINE_INTERVAL_1MONTH,
            '1 Week': Client.KLINE_INTERVAL_1WEEK,
            '1 Day': Client.KLINE_INTERVAL_1DAY,
            '4 Hours': Client.KLINE_INTERVAL_4HOUR,
            '1 Hour': Client.KLINE_INTERVAL_1HOUR,
            '15 Minutes': Client.KLINE_INTERVAL_15MINUTE,
            '5 Minutes': Client.KLINE_INTERVAL_5MINUTE,
            '1 Minute': Client.KLINE_INTERVAL_1MINUTE
        }
        selected_interval = st.selectbox(
            "Select Time Interval",
            list(intervals.keys()),
            index=list(intervals.keys()).index("1 Day")
        )
        
        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime(datetime.now().year, 1, 1)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now()
            )
    
    # Convert dates to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get crypto name
    crypto_names = {
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'BNB': 'Binance Coin',
        'XRP': 'Ripple',
        'ADA': 'Cardano',
        'DOGE': 'Dogecoin',
        'SOL': 'Solana',
        'DOT': 'Polkadot',
        'MATIC': 'Polygon',
        'AVAX': 'Avalanche',
        'LINK': 'Chainlink',
        'UNI': 'Uniswap',
        'ATOM': 'Cosmos',
        'LTC': 'Litecoin',
        'ETC': 'Ethereum Classic',
        'ALGO': 'Algorand',
        'XLM': 'Stellar',
        'FTM': 'Fantom',
        'NEAR': 'NEAR Protocol',
        'FIL': 'Filecoin',
        'TRX': 'TRON',
        'SHIB': 'Shiba Inu',
        'VET': 'VeChain',
        'SAND': 'The Sandbox',
        'MANA': 'Decentraland',
        'AAVE': 'Aave',
        'THETA': 'Theta Network',
        'AXS': 'Axie Infinity',
        'GRT': 'The Graph',
        'EGLD': 'Elrond'
    }
    selected_crypto = crypto_names.get(selected_symbol.replace('USDT', ''), selected_symbol)
    st.subheader(selected_crypto)
    
    # Main metrics
    current_price = get_current_price(selected_symbol)
    stats_24h = get_24h_stats(selected_symbol)
    
    if current_price and stats_24h:
        # Create container for metrics
        with st.container():
            # First row of metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Convert prices to selected currency
            current_price_converted = convert_price(current_price, "USD", currency_code)
            high_converted = convert_price(stats_24h['high'], "USD", currency_code)
            low_converted = convert_price(stats_24h['low'], "USD", currency_code)
            avg_converted = convert_price(stats_24h['weighted_avg_price'], "USD", currency_code)
            
            with col1:
                create_metric_card(
                    "Current Price",
                    format_price(current_price_converted, currency_code),
                    f"{stats_24h['price_change_percent']:.2f}%"
                )
            with col2:
                create_metric_card(
                    "24h High",
                    format_price(high_converted, currency_code)
                )
            with col3:
                create_metric_card(
                    "24h Low",
                    format_price(low_converted, currency_code)
                )
            with col4:
                create_metric_card(
                    "24h Weighted Avg",
                    format_price(avg_converted, currency_code)
                )
            
            # Second row of metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                volatility = ((stats_24h['high'] - stats_24h['low']) / stats_24h['low']) * 100
                create_metric_card(
                    "24h Volatility",
                    f"{volatility:.2f}",
                    suffix="%"
                )
            with col2:
                volume_btc = stats_24h['volume']
                create_metric_card(
                    "24h Volume (Crypto)",
                    f"{volume_btc:,.2f}",
                    suffix=f" {selected_symbol.replace('USDT', '')}"
                )
            with col3:
                volume_usd = stats_24h['quote_volume']
                create_metric_card(
                    "24h Volume (USD)",
                    f"{volume_usd:,.0f}",
                    prefix="$"
                )
            with col4:
                create_metric_card(
                    "24h Trades",
                    f"{stats_24h['count']:,}",
                    suffix=" trades"
                )

        # Add a separator with gradient
        st.markdown("""
            <div style="
                height: 2px;
                background: linear-gradient(90deg, 
                    rgba(255,255,255,0) 0%, 
                    rgba(255,255,255,0.1) 50%, 
                    rgba(255,255,255,0) 100%
                );
                margin: 2rem 0;
            "></div>
        """, unsafe_allow_html=True)
    
    # Chart section
    df = get_historical_data(selected_symbol, intervals[selected_interval], start_datetime, end_datetime)
    if df is not None:
        # Price chart (full width)
        st.plotly_chart(create_price_chart(df, currency_code), use_container_width=True)
        
        # Volume chart (full width)
        st.plotly_chart(create_volume_chart(df), use_container_width=True)
        
        # RSI and MACD in two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(create_rsi_chart(df), use_container_width=True)
            
        with col2:
            st.plotly_chart(create_macd_chart(df), use_container_width=True)
    
    # Volume and other statistics
    if stats_24h:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"24h Volume: {stats_24h['volume']:.2f} {selected_crypto.split(' - ')[0]}")
        with col2:
            st.info(f"24h USD Volume: ${stats_24h['quote_volume']:,.2f}")

if __name__ == "__main__":
    main()
