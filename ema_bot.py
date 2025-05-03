
import time
import http.client
import json
import pandas as pd
import schedule
from ta.trend import EMAIndicator
from colorama import init, Fore
import requests

init(autoreset=True)

API_HOST = "api.bybit.com"
HEADERS = {"User-Agent": "EMA-BOT/1.0"}

# 🔔 ALERTE TELEGRAM
def send_telegram(msg):
    token = "TON_BOT_TOKEN"
    chat_id = "TON_CHAT_ID"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception:
        pass

def api_request(path):
    conn = http.client.HTTPSConnection(API_HOST)
    conn.request("GET", path, headers=HEADERS)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    if not data:
        raise ValueError("Empty response from API")
    return json.loads(data)

def get_top_symbols(limit=500):
    path = "/v5/market/instruments-info?category=linear"
    data = api_request(path)
    symbols = data.get("result", {}).get("list", [])
    sorted_symbols = sorted(symbols, key=lambda x: float(x.get("volume24h", 0)), reverse=True)
    return [s["symbol"] for s in sorted_symbols if s["symbol"].endswith("USDT")][:limit]

def get_kline(symbol):
    path = f"/v5/market/kline?category=linear&symbol={symbol}&interval=240&limit=50"
    data = api_request(path)
    df = pd.DataFrame(data["result"]["list"])
    if df.shape[1] < 6:
        raise ValueError("Not enough data")
    df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    df['close'] = df['close'].astype(float)
    return df

def check_ema_cross(symbol):
    df = get_kline(symbol)
    ema9 = EMAIndicator(df['close'], window=9).ema_indicator()
    ema21 = EMAIndicator(df['close'], window=21).ema_indicator()
    if ema9.iloc[-1] < ema21.iloc[-1] and ema9.iloc[-2] >= ema21.iloc[-2]:
        print(Fore.GREEN + f"✔️ EMA 9 just crossed below EMA 21 on {symbol} (4H)")
        send_telegram(f"📉 EMA 9 crossed below EMA 21 on {symbol} (4H)")

def scan_top500():
    print("⏳ Scanning top 500 USDT Perp...")
    symbols = get_top_symbols()
    for symbol in symbols:
        try:
            check_ema_cross(symbol)
        except Exception:
            continue

# Toutes les 4h
schedule.every(4).hours.do(scan_top500)
print("🚀 EMA bot lancé — scan toutes les 4h sur le top 500 Bybit Perp.")
scan_top500()

while True:
    schedule.run_pending()
    time.sleep(1)
