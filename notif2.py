# === SCALPERGOLD (A2NK AIRDROPERS) ===
import requests
import pandas as pd
import ta
import time
import datetime

# === Konfigurasi ===
GOLDAPI_KEYS = [
    'API_KEY_1',
    'API_KEY_2',
    'API_KEY_3'
]
TELEGRAM_TOKEN = 'TOKEN-TELEGRAM'
TELEGRAM_CHAT_ID = 'CHAT-ID-GROUP'

TP_PERCENT = 0.003    # Take Profit +0.3%
SL_PERCENT = 0.0015   # Stop Loss -0.15%

# === Fungsi Kirim Telegram ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
    try:
        r = requests.post(url, data=payload)
        print(f"[Telegram] Dikirim: {msg}")
    except Exception as e:
        print(f"[Telegram] Gagal kirim: {e}")

# === Ambil harga XAU/USD dari GoldAPI dengan banyak API key ===
def get_xauusd_price():
    for api_key in GOLDAPI_KEYS:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {
            "x-access-token": api_key,
            "Content-Type": "application/json"
        }
        try:
            r = requests.get(url, headers=headers)
            data = r.json()
            if r.status_code == 200:
                price = data.get('price')
                print(f"[{datetime.datetime.now()}] Harga XAUUSD: {price} (API Key: {api_key})")
                return price
            else:
                print(f"[Harga] Gagal ambil data dengan API Key {api_key}. Status: {r.status_code}")
        except Exception as e:
            print(f"[Harga] Gagal ambil data dengan API Key {api_key}: {e}")
    print("[Harga] Semua API Key gagal.")
    return None

# === Inisialisasi Data Harga ===
price_history = []

# === Fungsi Deteksi Sinyal dengan RSI ===
def get_signal():
    price = get_xauusd_price()
    if not price:
        return None, None

    price_history.append(price)

    # Isi dummy data awal untuk membuat EMA & RSI valid
    if len(price_history) == 1:
        price_history[:] = [price - 1 + (i * 0.05) for i in range(60)]

    if len(price_history) < 60:
        print(f"[Data] Belum cukup data: {len(price_history)} candle")
        return None, None
    if len(price_history) > 150:
        price_history.pop(0)

    df = pd.DataFrame(price_history, columns=['close'])
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

    last = df.iloc[-1]
    print(f"[Sinyal] EMA20: {last['ema20']:.2f}, EMA50: {last['ema50']:.2f}, RSI: {last['rsi']:.2f}, Harga: {last['close']:.2f}")

    entry = last['close']
    if last['ema20'] > last['ema50'] and last['rsi'] < 70:
        tp = entry * (1 + TP_PERCENT)
        sl = entry * (1 - SL_PERCENT)
        return "BUY", (entry, tp, sl)
    elif last['ema20'] < last['ema50'] and last['rsi'] > 30:
        tp = entry * (1 - TP_PERCENT)
        sl = entry * (1 + SL_PERCENT)
        return "SELL", (entry, tp, sl)
    else:
        return None, None

# === Main Loop ===
print("🔁 Bot dimulai, uji sinyal EMA+RSI XAUUSD...\n")
while True:
    try:
        signal, levels = get_signal()
        if signal and levels:
            entry, tp, sl = levels
            msg = (
                f"Sinyal {signal} XAUUSD (EMA+RSI)\n"
                f"Entry: {entry:.2f}\n"
                f"TP: {tp:.2f}\n"
                f"SL: {sl:.2f}\n"
                f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            send_telegram(msg)
        time.sleep(300)  # Cek tiap 5 menit
    except Exception as e:
        print("⚠️ Error loop:", e)
        time.sleep(60)
