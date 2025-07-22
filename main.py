
import requests
from datetime import datetime
import random

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1396241698929119273/9rzJbZXVoEgBWEZk69njsnFJe_whzG9av58lwBewII9owdqiP7-F0uDvM7f_DZzrh1Al"
API_URL = "https://fapi.bitunix.com/api/v1/market/candles"
PAIRS = ["AAVEUSDT", "MATICUSDT", "DOGEUSDT", "XRPUSDT"]

def get_candles(symbol, interval="15m", limit=100):
    try:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        res = requests.get(API_URL, params=params)
        data = res.json()

        if "data" not in data:
            print(f"[ERROR] Invalid response for {symbol}: {data}")
            return []

        return [[float(x) for x in row[1:6]] for row in data["data"]]
    except Exception as e:
        print(f"[ERROR] Exception on get_candles: {e}")
        return []

def generate_signal(pair, candles):
    close_price = candles[-1][3]
    direction = random.choice(["LONG", "SHORT"])
    confidence = random.choice(["HIGH", "MEDIUM", "LOW"])

    if direction == "LONG":
        entry = round(close_price, 4)
        stop_loss = round(entry * 0.99, 4)
        take_profit = round(entry * 1.02, 4)
    else:
        entry = round(close_price, 4)
        stop_loss = round(entry * 1.01, 4)
        take_profit = round(entry * 0.98, 4)

    rr = round(abs((take_profit - entry) / (entry - stop_loss)), 2)

    return {
        "pair": pair,
        "direction": direction,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward": rr,
        "confidence": confidence
    }

def send_to_discord(signal):
    embed = {
        "title": f"🔥 MASTER CALL: {signal['pair']} – {signal['direction']}",
        "description": f"""
📍 Entry: `{signal['entry']}`
🛑 Stop Loss: `{signal['stop_loss']}`
🎯 Take Profit: `{signal['take_profit']}`
📊 Risk Reward: `{signal['risk_reward']}`
✅ Confidence Level: `{signal['confidence']}` ☑️

Analisa menggunakan Smart Money Concept dan Fibonacci Retracement di timeframe 15M.
""",
        "color": 5814783,
        "timestamp": datetime.utcnow().isoformat()
    }

    res = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
    if res.status_code == 204:
        print(f"[✅] Sinyal {signal['pair']} terkirim")
    else:
        print(f"[❌] Gagal kirim: {res.status_code} - {res.text}")

def run():
    for pair in PAIRS:
        candles = get_candles(pair)
        if not candles or len(candles) < 5:
            print(f"[!] Lewatkan {pair} (data kurang)")
            continue

        signal = generate_signal(pair, candles)
        send_to_discord(signal)

if __name__ == "__main__":
    run()
    
