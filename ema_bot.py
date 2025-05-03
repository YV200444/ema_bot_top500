import requests
import pandas as pd
import time
from datetime import datetime
import colorama
from colorama import Fore
colorama.init()

def api_request(path):
    try:
        url = f"https://api.bybit.com{path}"
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(Fore.RED + f"Erreur API : {e}" + Fore.RESET)
        return None

def get_top_symbols():
    data = api_request("/v5/market/tickers?category=linear")
    if data is None or "result" not in data:
        return []
    tickers = data["result"]["list"]
    top_symbols = [t["symbol"] for t in tickers if t["symbol"].endswith("USDT")]
    return top_symbols[200:500]  # top 200–500 uniquement

def get_klines(symbol, interval="15"):
    url = f"/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit=50"
    data = api_request(url)
    if data is None or "result" not in data:
        return None
    try:
        df = pd.DataFrame(data["result"]["list"])
        df.columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(Fore.RED + f"Erreur conversion dataframe pour {symbol} : {e}" + Fore.RESET)
        return None

def ema_indicator(df, window):
    return df["close"].ewm(span=window, adjust=False).mean()

def scan_top500():
    print(Fore.CYAN + "🚀 EMA bot lancé – scan immédiat du top 500 Bybit Perp" + Fore.RESET)
    print("📊 Scan en cours...")

    symbols = get_top_symbols()
    if not symbols:
        print(Fore.RED + "❌ Aucun symbole reçu du top 500." + Fore.RESET)
        return

    for symbol in symbols:
        df = get_klines(symbol)
        if df is None or len(df) < 21:
            continue

        ema_9 = ema_indicator(df, 9)
        ema_21 = ema_indicator(df, 21)

        if ema_9.iloc[-2] < ema_21.iloc[-2] and ema_9.iloc[-1] > ema_21.iloc[-1]:
            print(Fore.GREEN + f"💥 Cross HAUT détecté sur {symbol}" + Fore.RESET)
        elif ema_9.iloc[-2] > ema_21.iloc[-2] and ema_9.iloc[-1] < ema_21.iloc[-1]:
            print(Fore.RED + f"🔻 Cross BAS détecté sur {symbol}" + Fore.RESET)

# Lancement direct du scan à l'exécution du script
if __name__ == "__main__":
    scan_top500()
