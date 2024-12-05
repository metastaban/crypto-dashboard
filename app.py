import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import numpy as np
import requests
import cryptocompare
from datetime import datetime, timedelta

# Initialize CryptoCompare
# Ücretsiz API key almak için: https://min-api.cryptocompare.com/pricing
cryptocompare.cryptocompare._set_api_key_parameter('YOUR_API_KEY')  # İsteğe bağlı, API key olmadan da çalışır

# Cache timeout in seconds
CACHE_TIMEOUT = 60

# Initialize session state for caching
if 'last_update' not in st.session_state:
    st.session_state.last_update = {}
if 'cache' not in st.session_state:
    st.session_state.cache = {}

def get_cached_data(cache_key, fetch_func, timeout=CACHE_TIMEOUT):
    """Generic caching function"""
    current_time = time.time()
    if (cache_key not in st.session_state.cache or 
        cache_key not in st.session_state.last_update or 
        current_time - st.session_state.last_update[cache_key] > timeout):
        
        try:
            data = fetch_func()
            st.session_state.cache[cache_key] = data
            st.session_state.last_update[cache_key] = current_time
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None
            
    return st.session_state.cache[cache_key]

def get_crypto_list():
    """Fetches list of cryptocurrencies from CryptoCompare"""
    try:
        coins = cryptocompare.get_coin_list()
        return {f"{coin['Symbol'].upper()} - {coin['CoinName']}": coin['Symbol'] 
                for coin in coins.values() 
                if coin['Symbol'] and coin['CoinName']}
    except Exception as e:
        st.error(f"Error fetching cryptocurrency list: {str(e)}")
        return {}

def get_historical_data(symbol, vs_currency='USD', days=30):
    """Gets historical price data"""
    try:
        # Para birimi kodunu büyük harfe çevir
        vs_currency = vs_currency.upper()
        
        # Calculate timestamps
        now = datetime.now()
        if days == 'max':
            days = 2000  # yaklaşık 5.5 yıl
        elif isinstance(days, str):
            # Gün sayısını sayıya çevir
            days = int(days.lower().replace('d', ''))
        
        # Get historical daily data
        data = cryptocompare.get_historical_price_day(
            symbol.upper(),
            vs_currency,
            limit=days,
            exchange='CCCAGG'  # Aggregate of all exchanges
        )
        
        if not data:
            return None
            
        # Create DataFrame
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volumefrom': 'volume'
        })
        
        return df
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return None

def get_current_price(symbol, vs_currency='USD'):
    """Gets current price for the selected coin"""
    try:
        # Para birimi kodunu büyük harfe çevir
        vs_currency = vs_currency.upper()
        price = cryptocompare.get_price(symbol.upper(), currency=vs_currency)
        if price and symbol.upper() in price:
            return price[symbol.upper()][vs_currency]
        return None
    except Exception as e:
        st.error(f"Error fetching current price: {str(e)}")
        return None

def get_24h_stats(coin_id):
    """Get 24-hour statistics for a cryptocurrency"""
    try:
        # Get price data
        price_data = cryptocompare.get_price(coin_id, currency='USD', full=True)
        if not price_data or 'RAW' not in price_data or coin_id not in price_data['RAW'] or 'USD' not in price_data['RAW'][coin_id]:
            return None
            
        raw_data = price_data['RAW'][coin_id]['USD']
        
        return {
            'high': raw_data['HIGH24HOUR'],
            'low': raw_data['LOW24HOUR'],
            'volume': raw_data['VOLUME24HOUR'],
            'market_cap': raw_data['MKTCAP'],
            'price_change': raw_data['CHANGE24HOUR'],
            'price_change_percent': raw_data['CHANGEPCT24HOUR']
        }
    except Exception as e:
        print(f"Error fetching 24h stats: {e}")
        return None

def create_price_chart(df, currency_code="USD"):
    """Creates candlestick chart with the selected currency"""
    fig = go.Figure(data=[go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    )])
    
    fig.update_layout(
        title=f'Price Chart ({currency_code})',
        yaxis_title=f'Price ({currency_code})',
        template='plotly_dark',
        height=600,
        xaxis_rangeslider_visible=False
    )
    return fig

def create_volume_chart(df):
    """Creates volume chart"""
    fig = go.Figure(data=[go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        name="Volume",
        marker_color='rgba(0,150,255,0.5)'
    )])
    
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
    close_delta = df['close'].diff()
    
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    ma_up = up.ewm(com=14 - 1, adjust=True, min_periods=14).mean()
    ma_down = down.ewm(com=14 - 1, adjust=True, min_periods=14).mean()
    
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    
    fig = go.Figure(data=[go.Scatter(
        x=df['timestamp'],
        y=rsi,
        name="RSI",
        line=dict(color='yellow', width=1)
    )])
    
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
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=macd,
        name="MACD",
        line=dict(color='blue', width=1.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=signal,
        name="Signal",
        line=dict(color='orange', width=1.5)
    ))
    
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=histogram,
        name="Histogram",
        marker_color='rgba(255,255,255,0.3)'
    ))
    
    fig.update_layout(
        title='MACD (12,26,9)',
        yaxis_title='MACD',
        template='plotly_dark',
        height=200,
        margin=dict(t=30, l=60, r=60, b=30)
    )
    return fig

def create_metric_card(title, value, delta=None):
    """Creates a simple metric card"""
    if delta:
        delta_color = "#22c55e" if not str(delta).startswith('-') else "#ef4444"
        return f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-change {delta_color}">{delta}</div>
        </div>
        """
    else:
        return f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """

def create_metrics_section(current_price, stats_24h, selected_coin_id, currency_code):
    """Create the metrics section with current price and 24h stats"""
    
    # Add subheader with selected options
    st.markdown(f'<div class="subheader">{selected_coin_id}/{currency_code}</div>', unsafe_allow_html=True)
    
    return f"""
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">Current Price</div>
            <div class="metric-value">{format_price(current_price, currency_code)}</div>
            <div class="metric-change {'positive' if stats_24h['price_change_percent'] >= 0 else 'negative'}">{format_change(stats_24h['price_change_percent'])}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">24h High</div>
            <div class="metric-value">{format_price(stats_24h['high'], currency_code)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">24h Low</div>
            <div class="metric-value">{format_price(stats_24h['low'], currency_code)}</div>
        </div>
    </div>
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">24h Volume</div>
            <div class="metric-value">{format_volume(stats_24h['volume'], currency_code)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Market Cap</div>
            <div class="metric-value">{format_price(stats_24h['market_cap'], currency_code)}</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">24h Change</div>
            <div class="metric-value">{format_price(abs(stats_24h['price_change']), currency_code)}</div>
        </div>
    </div>
    """

def format_price(price, currency="USD"):
    """Formats price based on its value and currency"""
    if currency == "USD":
        symbol = "$"
    elif currency == "EUR":
        symbol = "€"
    else:
        symbol = currency + " "
    
    # Handle large numbers (billions, millions)
    if price >= 1_000_000_000:  # Billions
        return f"{symbol}{price/1_000_000_000:.2f}B"
    elif price >= 1_000_000:  # Millions
        return f"{symbol}{price/1_000_000:.2f}M"
    elif price >= 1_000:  # Thousands
        return f"{symbol}{price:,.2f}"
    else:
        # For small numbers, show more decimals if needed
        if price < 0.01:
            return f"{symbol}{price:.8f}"
        elif price < 1:
            return f"{symbol}{price:.4f}"
        else:
            return f"{symbol}{price:,.2f}"

def format_change(value):
    """Formats percentage change values"""
    return f"{value:+.2f}%" if value else "0.00%"

def format_volume(volume, currency="USD"):
    """Formats volume with appropriate suffixes"""
    if currency == "USD":
        symbol = "$"
    elif currency == "EUR":
        symbol = "€"
    else:
        symbol = currency + " "
    
    if volume >= 1_000_000_000:  # Billions
        return f"{symbol}{volume/1_000_000_000:.2f}B"
    elif volume >= 1_000_000:  # Millions
        return f"{symbol}{volume/1_000_000:.2f}M"
    else:
        return f"{symbol}{volume:,.0f}"

def main():
    # Set page config for favicon and title
    st.set_page_config(
        page_title="Crypto Dashboard",
        page_icon="🚀",  # Geçici olarak bir emoji kullanıyoruz
        layout="wide"
    )
    
    st.title("Cryptocurrency Dashboard")
    
    # Add custom styling
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
        }
        .main {
            padding: 0;
            max-width: 100%;
        }
        .block-container {
            max-width: 100%;
            padding: 1rem;
        }
        h1 {
            color: white;
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .subheader {
            color: white;
            font-size: 1.2rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
        }
        .sidebar-logo {
            display: block;
            margin: 0 auto 1rem auto;
            width: 80px;
        }
        
        /* Metric Cards Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0;
            width: 100%;
        }
        
        /* Responsive Grid */
        @media screen and (max-width: 1200px) {
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media screen and (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            .block-container {
                padding: 0.5rem;
            }
            .metric-card {
                padding: 1rem;
            }
            h1 {
                font-size: 1.5rem;
                margin-bottom: 1rem;
            }
        }
        
        /* Metric Card */
        .metric-card {
            background: linear-gradient(145deg, #1E1E1E, #2D2D2D);
            border-radius: 10px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .metric-title {
            color: #808080;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            color: white;
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            word-break: break-word;
        }
        
        .metric-change {
            font-size: 0.9rem;
        }
        
        .metric-change.positive {
            color: #22c55e;
        }
        
        .metric-change.negative {
            color: #ef4444;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

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
        crypto_list = get_crypto_list()
        if not crypto_list:
            st.error("Unable to fetch cryptocurrency list")
            st.stop()
            
        # Find and set BTC as default
        default_index = 0
        crypto_names = list(crypto_list.keys())
        for i, name in enumerate(crypto_names):
            if name.startswith('BTC -'):
                default_index = i
                break
        
        selected_crypto = st.selectbox("Select Cryptocurrency:", crypto_names, index=default_index)
        selected_coin_id = crypto_list[selected_crypto]
        
        # Currency selection
        currencies = {
            "US Dollar": "USD",
            "Euro": "EUR",
            "British Pound": "GBP",
            "Japanese Yen": "JPY",
            "Turkish Lira": "TRY"
        }
        
        selected_currency = st.selectbox(
            "Select Currency",
            list(currencies.keys()),
            index=0
        )
        currency_code = currencies[selected_currency]
        
        # Time interval selection
        intervals = {
            '1 Day': 1,
            '7 Days': 7,
            '30 Days': 30,
            '90 Days': 90,
            '180 Days': 180,
            '1 Year': 365,
            'Max': 'max'
        }
        
        selected_interval = st.selectbox(
            "Select Time Interval",
            list(intervals.keys()),
            index=2
        )
        days = intervals[selected_interval]
        
    # Get current price and stats
    current_price = get_current_price(selected_coin_id, currency_code)
    stats_24h = get_24h_stats(selected_coin_id)
    
    if current_price and stats_24h:
        metrics_html = create_metrics_section(current_price, stats_24h, selected_coin_id, currency_code)
        st.markdown(metrics_html, unsafe_allow_html=True)
    else:
        st.error("Could not fetch price data. Please try again.")
    
    # Get and display historical data
    df = get_historical_data(selected_coin_id, currency_code, days)
    if df is not None:
        # Create tabs for different charts
        tab1, tab2, tab3, tab4 = st.tabs(["Price", "Volume", "RSI", "MACD"])
        
        with tab1:
            st.plotly_chart(create_price_chart(df, currency_code), use_container_width=True)
        
        with tab2:
            st.plotly_chart(create_volume_chart(df), use_container_width=True)
        
        with tab3:
            st.plotly_chart(create_rsi_chart(df), use_container_width=True)
        
        with tab4:
            st.plotly_chart(create_macd_chart(df), use_container_width=True)

if __name__ == "__main__":
    main()
