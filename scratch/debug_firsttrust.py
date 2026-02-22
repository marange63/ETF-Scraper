import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(
    "https://www.ftportfolios.com/Retail/Etf/EtfHoldings.aspx?Ticker=CIBR",
    headers=HEADERS, timeout=60
)
soup = BeautifulSoup(response.text, 'html.parser')

EXPECTED_HEADERS = {'Security Name', 'Identifier', 'Weighting'}

for i, table in enumerate(soup.find_all('table')):
    rows = table.find_all('tr', recursive=False)  # direct children only
    if not rows:
        continue
    first_row_cells = [td.get_text(strip=True) for td in rows[0].find_all(['td', 'th'], recursive=False)]
    if EXPECTED_HEADERS.issubset(set(first_row_cells)):
        print(f"Table {i}: headers = {first_row_cells}")
        print(f"  {len(rows)} direct rows")
        if len(rows) > 1:
            print(f"  Row 1: {[td.get_text(strip=True) for td in rows[1].find_all(['td','th'], recursive=False)]}")
        break
