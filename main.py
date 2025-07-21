from fastapi import FastAPI
import requests, time, asyncio
from datetime import datetime
import numpy as np
import uvicorn

app = FastAPI()

# ===== CONFIG =====
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'
DISCORD_WEBHOOK_URL = 'YOUR_DISCORD_WEBHOOK_URL'

# ALTCOIN LIST - tambahkan sesuai kebutuhan
SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'MATICUSDT',
    'AVAXUSDT', 'DOGEUSDT', 'OPUSDT', 'LTCUSDT', 'AAVEUSDT',
    'ARBUSDT', 'SUIUSDT', 'BLURUSDT', 'INJUSDT', 'RNDRUSDT',
    'PEPEUSDT', 'FLOKIUSDT', 'BCHUSDT', 'GRTUSDT', 'APTUSDT'
]

TIMEFRAMES = ['15m', '4h']

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def send_discord(message):
    data = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def get_candles(symbol, interval, limit=100):
    url = f"https://api.bitunix.com/api/v1/market/kline?symbol={symbol}&interval={interval}&limit={limit}"
    res = requests.get(url)
    data = res.json()
    return data['data']

def analyze_trend(candles):
    closes = [float(c[4]) for c in candles]
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]

    higher_highs = highs[-3:] == sorted(highs[-3:], reverse=True)
    lower_lows = lows[-3:] == sorted(lows[-3:])
    structure = 'BULLISH' if higher_highs else 'BEARISH' if lower_lows else 'RANGING'

    fib_low, fib_high = min(lows[-20:]), max(highs[-20:])
    fib_levels = {
        '0.618': fib_high - (fib_high - fib_low) * 0.618,
        '0.5': fib_high - (fib_high - fib_low) * 0.5
    }

    return structure, closes[-1], fib_levels

def get_confidence_level(tf15, tf4h, rr, entry, sl, tp):
    confidence = "MEDIUM"
    if tf15 == tf4h:
        confidence = "HIGH"
        rr_factor = rr >= 2
        entry_near_fib = abs(entry - sl) / entry < 0.03
        if rr_factor and entry_near_fib:
            confidence = "HIGH ✅"
        elif rr > 1.5:
            confidence = "MEDIUM ☑️"
        else:
            confidence = "LOW ⚠️"
    else:
        confidence = "LOW ⚠️"
    return confidence

def generate_master_call(symbol):
    try:
        results = {}
        for tf in TIMEFRAMES:
            candles = get_candles(symbol, tf)
            structure, last_price, fib = analyze_trend(candles)
            results[tf] = {"structure": structure, "price": last_price, "fib": fib}

        tf15 = results['15m']['structure']
        tf4h = results['4h']['structure']

        if tf15 == tf4h and tf15 != 'RANGING':
            direction = "LONG" if tf15 == "BULLISH" else "SHORT"
            entry = results['15m']['price']
            fib = results['15m']['fib']
            sl = round(fib['0.618'] if direction == "LONG" else fib['0.5'], 4)
            tp = round(entry * (1.03 if direction == "LONG" else 0.97), 4)
            rr = round(abs(tp - entry) / abs(entry - sl), 2)
            confidence = get_confidence_level(tf15, tf4h, rr, entry, sl, tp)

            message = f"""
🔥 MASTER CALL: {symbol} – {direction}

📍 Entry: {entry}
🛑 Stop Loss: {sl}
🎯 Take Profit: {tp}
📊 Risk Reward: {rr}
✅ Confidence Level: {confidence}

Sinyal berdasarkan konfirmasi arah tren timeframe 15M & 4H (SMC+Fibonacci).
            """.strip()

            send_telegram(message)
            send_discord(message)
            print(f"[{datetime.now()}] ✅ Sent signal for {symbol}")
        else:
            print(f"[{datetime.now()}] ❌ No valid trend for {symbol}")
    except Exception as e:
        print(f"⚠️ Error for {symbol}: {e}")

async def scheduler_loop():
    while True:
        print(f"🔁 Running analysis at {datetime.now()}...
")
        for symbol in SYMBOLS:
            generate_master_call(symbol)
            await asyncio.sleep(1.5)
        await asyncio.sleep(3 * 60 * 60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduler_loop())

@app.get("/run")
def manual_run():
    for symbol in SYMBOLS:
        generate_master_call(symbol)
    return {"status": "ok", "message": "All signals checked manually."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
