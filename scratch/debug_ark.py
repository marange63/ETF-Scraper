import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://assets.ark-funds.com/fund-documents/funds-etf-csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv"
response = requests.get(url, headers=HEADERS, timeout=60)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
print()
print(response.text[:2000])
