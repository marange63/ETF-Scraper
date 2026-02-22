import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

csv_url = "https://assets.globalxetfs.com/funds/holdings/botz_full-holdings_20260220.csv"
r = requests.get(csv_url, headers=HEADERS, timeout=60)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type','?')}")
print()
print(r.text[:2000])
