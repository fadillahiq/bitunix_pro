import requests

BASE_URL = "https://api.bitunix.com"
PAIR = "aaveusdt"
INTERVAL = "15m"

def test_bitunix_api():
    url = f"{BASE_URL}/v1/market/kline"
    params = {"symbol": PAIR, "interval": INTERVAL, "limit": 5}
    res = requests.get(url, params=params)
    print("Status Code:", res.status_code)
    print("Response Text:\n", res.text)

test_bitunix_api()
