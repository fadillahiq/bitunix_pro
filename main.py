
import requests
from datetime import datetime

# === CONFIGURATION ===
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1396241698929119273/9rzJbZXVoEgBWEZk69njsnFJe_whzG9av58lwBewII9owdqiP7-F0uDvM7f_DZzrh1Al"
PAIRS = ["AAVEUSDT", "MATICUSDT", "XRPUSDT"]
TIMEFRAME = "15m"
BASE_URL = "https://fapi.bitunix.com"

# === GET CANDLE DATA FROM BITUNIX ===
def get_candles(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/api/v1/contract/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    res = requests.get(url, params=params)

    try:
        data = res.json()
    except Exception as e:
        print(f"[ERROR] JSON decode failed: {e}")
        print("Raw Response:", res.text)
        return []

    if "data" not in data or not isinstance(data["data"], list):
        print(f"[ERROR] Unexpected response: {data}")
        return []

    candles = []
    for row in data["data"]:
        try:
            # Expected format: [timestamp, open, high, low, close, volume]
            candles.append([float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])])
        except Exception as e:
            print(f"[ERROR] Parsing candle failed: {row}, error: {e}")
            continue

    return candles

# === SMART MONEY + FIBONACCI STRATEGY ===
def analyze_smc_fibo(candles):
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    close = candles[-1][4]

    swing_high = max(highs[-20:])
    swing_low = min(lows[-20:])

    fib_618 = swing_low + 0.618 * (swing_high - swing_low)
    fib_50 = swing_low + 0.5 * (swing_high - swing_low)

    bos_up = close > swing_high
    bos_down = close < swing_low

    signal = None
    if bos_up and close > fib_618:
        signal = {
            "type": "LONG",
            "entry": round(close, 2),
            "sl": round(fib_50, 2),
            "tp": round(close + (close - fib_50) * 1.5, 2),
            "confidence": "HIGH"
        }
    elif bos_down and close < fib_618:
        signal = {
            "type": "SHORT",
            "entry": round(close, 2),
            "sl": round(fib_50, 2),
            "tp": round(close - (fib_50 - close) * 1.5, 2),
            "confidence": "HIGH"
        }

    return signal

# === SEND TO DISCORD ===
def send_discord_signal(pair, signal):
    rr = round(abs(signal["tp"] - signal["entry"]) / abs(signal["entry"] - signal["sl"]), 2)
    content = f"""
🔥 **MASTER CALL: {pair} – {signal['type']}**

📍 Entry: `{signal['entry']}`
🛑 Stop Loss: `{signal['sl']}`
🎯 Take Profit: `{signal['tp']}`
📊 Risk Reward: `{rr}`
✅ Confidence Level: `{signal['confidence']} ☑️`

Analisis berdasarkan:
- Smart Money Concept (BOS + Struktur)
- Fibonacci Retracement 0.5 & 0.618
- Timeframe: {TIMEFRAME}
    """.strip()

    requests.post(DISCORD_WEBHOOK_URL, json={"content": content})

# === MAIN EXECUTION ===
def run():
    for pair in PAIRS:
        candles = get_candles(pair)
        if not candles or len(candles) < 20:
            continue
        signal = analyze_smc_fibo(candles)
        if signal:
            send_discord_signal(pair, signal)

# Run once
run()
