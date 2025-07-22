
import requests, time
from datetime import datetime

# === CONFIGURATION ===
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1396241698929119273/9rzJbZXVoEgBWEZk69njsnFJe_whzG9av58lwBewII9owdqiP7-F0uDvM7f_DZzrh1Al"
PAIRS = ["AAVEUSDT", "MATICUSDT", "XRPUSDT"]  # Altcoin stabil
TIMEFRAME = "15m"
BASE_URL = "https://api.bitunix.com"

# === FUNCTION TO GET CANDLESTICK DATA ===
def get_candles(symbol, interval="15m", limit=100):
    url = f"{BASE_URL}/v1/market/kline"
    params = {"symbol": symbol.lower(), "interval": interval, "limit": limit}
    res = requests.get(url, params=params).json()
    candles = res.get("data", [])
    return [[float(c) for c in item] for item in candles]

# === SMART MONEY + FIBONACCI STRATEGY ===
def analyze_smc_fibo(candles):
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    close = candles[-1][4]

    swing_high = max(highs[-20:])
    swing_low = min(lows[-20:])

    fib_618 = swing_low + 0.618 * (swing_high - swing_low)
    fib_50 = swing_low + 0.5 * (swing_high - swing_low)

    # Detect BOS (Break of Structure) simple version
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

# === MAIN LOOP ===
def run():
    for pair in PAIRS:
        candles = get_candles(pair)
        if not candles:
            continue
        signal = analyze_smc_fibo(candles)
        if signal:
            send_discord_signal(pair, signal)

# Run once or schedule as needed
run()
