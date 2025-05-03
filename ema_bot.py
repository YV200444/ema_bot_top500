import requests
import pandas as pd
import schedule
import time
from ta.trend import EMAIndicator
from colorama import Fore, Style
import os

# === CONFIG ===
API_KEY = "votre_clef_api_bybit"  # À remplacer si besoin
TELEGRAM_TOKEN = "8039833735:AAFwuBUQgNKB9TEA9l4uIYBitzyCO4I5CKE"
CHAT_ID = "6233846415"
SYMBOL_COUNT = 500  # Nombre d'altcoins à scanner
TIMEFRAME = "1h"  # timeframe des bougies

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Erreur Telegram:", e)

def api_request(path):
    url = f"https://api.bybit.com{path}"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print("Erreur API:", e)
        return {}

def get_top_symbols():
    path = "/v5/market/tickers?category=linear"
    data = api_request(path)
    try:
        tickers = data["result"]["list"]
        usdt_pairs = [t["symbol"] for t in tickers if "USDT" in t["symbol"] and "PERP" in t["symbol"]]
        return usdt_pairs[:SYMBOL_COUNT]
    except:
        print("Erreur récupération des paires.")
        return []

def get_ema_cross(symbol):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={TIMEFRAME}&limit=100"
    data = api_request(url)
    try:
        df = pd.DataFrame(data["result"]["list"])
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "_"]
        df["close"] = pd.to_numeric(df["close"])
        ema_9 = EMAIndicator(close=df["close"], window=9).ema_indicator()
        ema_21 = EMAIndicator(close=df["close"], window=21).ema_indicator()
        if ema_9.iloc[-2] < ema_21.iloc[-2] and ema_9.iloc[-1] > ema_21.iloc[-1]:
            return "cross_up"
        elif ema_9.iloc[-2] > ema_21.iloc[-2] and ema_9.iloc[-1] < ema_21.iloc[-1]:
            return "cross_down"
        else:
            return "no_cross"
    except Exception as e:
        print(f"{symbol} erreur EMA:", e)
        return "error"

def scan_top500():
    print("🔍 Scanning top 500 USDT Perp...")
    symbols = get_top_symbols()
    for symbol in symbols:
        result = get_ema_cross(symbol)
        if result == "cross_up":
            print(Fore.GREEN + f"📈 CROSS UP: {symbol}" + Style.RESET_ALL)
            send_telegram_alert(f"📈 EMA 9/21 CROSS UP: {symbol}")
        elif result == "cross_down":
            print(Fore.RED + f"📉 CROSS DOWN: {symbol}" + Style.RESET_ALL)
            send_telegram_alert(f"📉 EMA 9/21 CROSS DOWN: {symbol}")
        else:
            pass  # pas d'action

print("🚀 EMA bot lancé – scan toutes les 4h sur le top 500 Bybit Perp.")
schedule.every(4).hours.do(scan_top500)

# Premier scan direct au démarrage
scan_top500()

while True:
    schedule.run_pending()
    time.sleep(1)
