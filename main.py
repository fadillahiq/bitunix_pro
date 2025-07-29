import requests
import time
from datetime import datetime
import schedule

# DISCORD
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1396241698929119273/9rzJbZXVoEgBWEZk69njsnFJe_whzG9av58lwBewII9owdqiP7-F0uDvM7f_DZzrh1Al"

# PAIRS
PAIRS = ["HBARUSDT", "PENGUUSDT", "DOGEUSDT", "TAOUSDT", "ETHUSDT"]

# GET KLINE
def get_klines(pair, interval="15m", limit=50):
    url = f"https://fapi.bitunix.com/api/v1/contract/quote/klines?symbol={pair}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        return data.get("data", [])
    except:
        return []

# DETECT SMC + PA
def detect_smc_signal(kline_items, pair):
    candles = [{
        "time": int(k["time"]),
        "open": float(k["open"]),
        "high": float(k["high"]),
        "low": float(k["low"]),
        "close": float(k["close"]),
        "volume": float(k["baseVol"])
    } for k in kline_items]

    if len(candles) < 20:
        return None

    last = candles[-1]
    prev = candles[-2]

    last_close = last["close"]
    last_open = last["open"]
    prev_close = prev["close"]
    prev_open = prev["open"]

    # Engulfing Pattern
    bullish_engulfing = last_close > last_open and prev_close < prev_open and last_close > prev_open and last_open < prev_close
    bearish_engulfing = last_close < last_open and prev_close > prev_open and last_close < prev_open and last_open > prev_close

    # Struktur harga
    highs = [c["high"] for c in candles[-6:-1]]
    lows = [c["low"] for c in candles[-6:-1]]
    swing_high = max(highs)
    swing_low = min(lows)

    # BOS
    valid_bullish_bos = bullish_engulfing and last_close > swing_high
    valid_bearish_bos = bearish_engulfing and last_close < swing_low

    # Setup Entry
    if valid_bullish_bos:
        entry = last_close
        sl = swing_low
        tp = round(entry + (entry - sl) * 2, 6)
        rr = round((tp - entry) / (entry - sl), 2)
        confidence = "HIGH" if rr >= 2 else "MEDIUM"

        return f"""
🔥 MASTER CALL: {pair.upper()} – LONG

📍 Entry: {entry}
🛑 Stop Loss: {sl}
🎯 Take Profit: {tp}
📊 Risk Reward: {rr}
✅ Confidence Level: {confidence} ☑️

Sinyal berdasarkan Smart Money Concept dan Price Action:
- Break of Structure (BOS) terkonfirmasi.
- Pola Bullish Engulfing valid sebagai sinyal reversal.
- Entry mengikuti momentum dan validasi struktur pasar (HH–HL).

🎯 Rekomendasi: Pantau konfirmasi lanjutan atau entry segera jika harga retest.
        """.strip()

    elif valid_bearish_bos:
        entry = last_close
        sl = swing_high
        tp = round(entry - (sl - entry) * 2, 6)
        rr = round((entry - tp) / (sl - entry), 2)
        confidence = "HIGH" if rr >= 2 else "MEDIUM"

        return f"""
🔥 MASTER CALL: {pair.upper()} – SHORT

📍 Entry: {entry}
🛑 Stop Loss: {sl}
🎯 Take Profit: {tp}
📊 Risk Reward: {rr}
✅ Confidence Level: {confidence} ☑️

Sinyal berdasarkan Smart Money Concept dan Price Action:
- Break of Structure (BOS) turun terkonfirmasi.
- Pola Bearish Engulfing valid sebagai sinyal reversal.
- Entry mengikuti momentum dan validasi struktur pasar (LH–LL).

🎯 Rekomendasi: Entry segera atau tunggu retest ke area supply.
        """.strip()

    return None

# KIRIM KE DISCORD
def send_to_discord(message):
    data = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        print("❌ Gagal kirim:", e)

# MAIN
def run_signal_bot():
    print(f"\n🚀 Mengecek sinyal valid berdasarkan SMC... {datetime.now().strftime('%H:%M:%S')} WIB")
    best_signal = None

    for pair in PAIRS:
        klines = get_klines(pair)
        if not klines:
            continue
        signal = detect_smc_signal(klines, pair)
        if signal:
            best_signal = signal
            break  # kirim sinyal terbaik pertama yang valid

    if best_signal:
        send_to_discord(best_signal)
        print("✅ Sinyal dikirim!")
    else:
        send_to_discord("tidak ada sinyal valid saat ini")
        print("❌ Tidak ada sinyal valid.")

# JADWAL TIAP 3 JAM
schedule.every(3).hours.do(run_signal_bot)

print("🤖 Bot sinyal crypto siap jalan (tiap 3 jam)...")
run_signal_bot()

while True:
    schedule.run_pending()
    time.sleep(60)
