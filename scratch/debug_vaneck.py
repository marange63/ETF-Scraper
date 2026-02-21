import requests
from io import BytesIO, StringIO
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://www.vaneck.com/us/en/investments/uranium-nuclear-energy-etf-nlr/downloads/holdings/"
response = requests.get(url, headers=HEADERS, timeout=60, allow_redirects=True)

print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
print(f"Final URL: {response.url}")
print()

content_type = response.headers.get("Content-Type", "")
if "spreadsheetml" in content_type or "excel" in content_type:
    print("=== Excel file detected ===")
    df_raw = pd.read_excel(BytesIO(response.content), header=None, engine='openpyxl')
    print("First 10 rows (no header):")
    print(df_raw.head(10).to_string())
else:
    print("=== Non-Excel response ===")
    print("First 1000 chars:")
    print(response.text[:1000])
    print()
    # Try parsing as CSV to see columns
    try:
        df = pd.read_csv(StringIO(response.text))
        print("Columns:", df.columns.tolist())
        print(df.head())
    except Exception as e:
        print(f"CSV parse failed: {e}")
