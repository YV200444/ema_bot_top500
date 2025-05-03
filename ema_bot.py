import requests
import time
import schedule
import pandas as pd
import json
from ta.trend import EMAIndicator
from colorama import Fore, Style

# ---------------- CONFIG ----------------
API_URL = "https://api.bybit.com/v5/market/tickers?category=linear"
TOP_LIMIT = 500
SCAN_INTERVAL_HOURS = 4
# ---------------------------------------

def api_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Réponse API brute :", response.text[:100])  # pour debug
        return json.loads(response.text)
    except Exception as e:
        print("Erreur lors de la requête API :", e)
        return {}

def get_top_symbols():
    data = api_request(API_URL)
    if not data or "result" not in data or "list" not in data["result"]:
        print("⚠️ Aucune donnée reçue de l'API.")
        return []

    symbols = []
    for item in data["result"]["list"]:
        symbol = item["symbol"]
        if "USDT" in symbol:
            symbols.append(symbol)
        if len(symbols) >= TOP_LIMIT:
            break
    return symbols

def fetch_ohlcv(symbol):
    url = f"https://api.bybit.com/v5/market/kline?category=linear&interval=240&symbol={symbol}&limit=50"
    data = api_request(url)
    try:
        return pd.DataFrame(data["result"]["list"], columns=[
            "timestamp", "open", "high", "low", "close", "volume", "turnover"
        ])
    except:
        return pd.DataFrame()

def analyze_ema_cross(df):
    try:
        df["close"] = pd.to_numeric(df["close"])
        df["ema_9"] = EMAIndicator(df["close"], window=9).ema_indicator()
        df["ema_21"] = EMAIndicator(df["close"], window=21).ema_indicator()
        if df["ema_9"].iloc[-2] > df["ema_21"].iloc[-2] and df["ema_9"].iloc[-1] < df["ema_21"].iloc[-1]:
            return True
    except Exception as e:
        print("Erreur analyse EMA :", e)
    return False

def scan_top500():
    print("🚀 EMA bot lancé – scan toutes les 4h sur le top 500 Bybit Perp.")
    print("📊 Scanning top 500 USDT Perp...")
    symbols = get_top_symbols()
    for symbol in symbols:
        df = fetch_ohlcv(symbol)
        if df.empty:
            print(f"Erreur sur {symbol} : données vides.")
            continue
        if analyze_ema_cross(df):
            print(Fore.GREEN + f"✅ CROISEMENT sur {symbol} — EMA 9 passe sous EMA 21 !" + Style.RESET_ALL)

# Planifie le scan toutes les 4h
schedule.every(SCAN_INTERVAL_HOURS).hours.do(scan_top500)

# Lancement immédiat au boot
scan_top500()

while True:
    schedule.run_pending()
    time.sleep(1)
