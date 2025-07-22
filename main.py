import requests, time, schedule
from datetime import datetime

BOT_TOKEN = "7580552170:AAEGs8Z4HVhZgtnzRaK4VctZe6_fUL0pkz8"
CHAT_ID = "5246334675"

PAIRS = [
    "ETHUSDT", "BTCUSDT", "AAVEUSDT", "DOGEUSDT", "XRPUSDT",
    "MATICUSDT", "SUIUSDT", "OPUSDT", "HBARUSDT", "PEPEUSDT",
    "ARBUSDT", "INJUSDT", "RNDRUSDT", "LINKUSDT", "NEARUSDT"
]

API = "https://fapi.bitunix.com/api/v1/futures/market/kline"

def get_klines(symbol, interval="15m", limit=50):
    try:
        r = requests.get(API, params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
        d = r.json()
        if d.get("code") == 0 and isinstance(d.get("data"), list):
            return d["data"]
    except: pass
    return []

def detect_signal(symbol):
    k = get_klines(symbol)
    if not k: return None
    try:
        closes = [float(i["close"]) for i in k]
        highs = [float(i["high"]) for i in k]
        lows  = [float(i["low"]) for i in k]

        if len(closes) < 20: return None

        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        last_close = closes[-1]

        fib_0 = recent_high
        fib_1 = recent_low
        diff = fib_0 - fib_1

        fib_382 = fib_0 - 0.382 * diff
        fib_50 = fib_0 - 0.5 * diff
        fib_618 = fib_0 - 0.618 * diff

        # Kondisi LONG (breakout atas + harga di atas fib50 + valid TP target)
        if last_close > recent_high * 0.995 and last_close > fib_50:
            sl = round(fib_618, 4)
            tp = round(last_close + diff * 1.618, 4)
            return {"symbol": symbol, "side": "LONG", "entry": last_close, "sl": sl, "tp": tp}

        # Kondisi SHORT (break bawah + harga di bawah fib50 + valid TP target)
        if last_close < recent_low * 1.005 and last_close < fib_50:
            sl = round(fib_618, 4)
            tp = round(last_close - diff * 1.618, 4)
            return {"symbol": symbol, "side": "SHORT", "entry": last_close, "sl": sl, "tp": tp}
    except: pass
    return None

def format_call(sig):
    rr = round(abs(sig['tp'] - sig['entry']) / abs(sig['entry'] - sig['sl']), 2)
    confidence = "HIGH" if rr > 2.5 else "MEDIUM" if rr > 1.5 else "LOW"
    return f"""🔥 MASTER CALL: {sig['symbol']} – {sig['side']}

📍 Entry: {sig['entry']}
🛑 Stop Loss: {sig['sl']}
🎯 Take Profit: {sig['tp']}
📊 Risk Reward: {rr}
💯 Confidence Level: {confidence} ✅

BITUNIX PRO
"""

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def job():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Menganalisis...")
    signals = [detect_signal(p) for p in PAIRS]
    valids = [s for s in signals if s]
    if valids:
        for sig in valids:
            msg = format_call(sig)
            send_to_telegram(msg)
            print(f"Sinyal dikirim: {sig['symbol']} - {sig['side']}")
    else:
        print("Tidak ada sinyal valid.")

# Jalankan sekali di awal
job()

# Jadwalkan setiap 3 jam
schedule.every(180).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
