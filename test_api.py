from pycoingecko import CoinGeckoAPI
import time

cg = CoinGeckoAPI()

try:
    print("Testing CoinGecko API...")
    
    # Test 1: Get coin list
    print("\nTest 1: Fetching coin list...")
    coins = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=100, sparkline=False)
    print(f"Successfully fetched {len(coins)} coins")
    
    # Wait a bit to avoid rate limiting
    time.sleep(1)
    
    # Test 2: Get Bitcoin data
    print("\nTest 2: Fetching Bitcoin data...")
    btc_data = cg.get_coin_market_chart_by_id(id='bitcoin', vs_currency='usd', days=1)
    print(f"Successfully fetched Bitcoin data with {len(btc_data['prices'])} price points")
    
    # Wait a bit to avoid rate limiting
    time.sleep(1)
    
    # Test 3: Get current price
    print("\nTest 3: Fetching current prices...")
    current_price = cg.get_price(ids=['bitcoin', 'ethereum'], vs_currencies='usd')
    print(f"Current prices: {current_price}")

except Exception as e:
    print(f"\nError occurred: {str(e)}")
