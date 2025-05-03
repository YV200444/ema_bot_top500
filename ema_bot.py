import requests
import json
import pandas as pd
import time
import schedule
from datetime import datetime
from colorama import Fore, Style

# === CONFIGURATION ===
TELEGRAM_TOKEN = "8039833735:AAFwuBUQgNKB9TEA9l4uIYBitzyCO4I5CKE"
TELEGRAM_CHAT_ID = "6233846415"
SCAN_INTERVAL_HOURS = 4

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur envoi Telegram: {e}")

def api_request(path):
    base_url = "https://api.bybit.com"
    response = requests.get(base_url + path)
    return json.loads(response.text)

def get_top_symbols():
    path = "/v5/market/tickers?category=linear"
    data = api_request(path)
    tickers = data["result"]["list"]
    sorted_tickers = sorted(tickers, key=lambda x: float(x["volume24h"]), reverse=True)
    symbols = [x["symbol"] for x in sorted_tickers if "USDT" in x["symbol"]]
    return symbols[200:500]  # Top 200–500 uniquement

def get_klines(symbol):
    path = f"/v5/market/kline?category=linear&symbol={symbol}&interval=15&limit=150"
    data = api_request(path)
    try:
        df = pd.DataFrame(data["result"]["list"], columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"])
        df["close"] = df["close"].astype(float)
        return df
    except:
        return None

def ema_indicator(df, window):
    return df["close"].ewm(span=window, adjust=False).mean()

def check_signal(symbol):
    df = get_klines(symbol)
    if df is None or len(df) < 50:
        return
    ema_9 = ema_indicator(df, 9)
    ema_21 = ema_indicator(df, 21)
    if ema_9.iloc[-2] < ema_21.iloc[-2] and ema_9.iloc[-1] > ema_21.iloc[-1]:
        msg = f"✅ EMA 9/21 BULLISH CROSS on {symbol} (15min)"
        print(Fore.GREEN + msg + Style.RESET_ALL)
        send_telegram_alert(msg)
    elif ema_9.iloc[-2] > ema_21.iloc[-2] and ema_9.iloc[-1] < ema_21.iloc[-1]:
        msg = f"❌ EMA 9/21 BEARISH CROSS on {symbol} (15min)"
        print(Fore.RED + msg + Style.RESET_ALL)
        send_telegram_alert(msg)

def scan_top500():
    print("🚀 EMA bot lancé – scan toutes les 4h sur le top 500 Bybit Perp.")
    print("⏳ Scanning top 500 USDT Perp...")
    symbols = get_top_symbols()
    for symbol in symbols:
        time.sleep(0.2)
        check_signal(symbol)

schedule.every(SCAN_INTERVAL_HOURS).hours.do(scan_top500)

# === Lancement initial immédiat ===
scan_top500()

while True:
    schedule.run_pending()
    time.sleep(1)
