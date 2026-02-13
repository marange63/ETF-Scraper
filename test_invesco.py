import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
})

# Try the REST API endpoint
rest_url = 'https://www.invesco.com/us-rest/contentdetail?contentId=d72407c649400410VgnVCM10000046f1bf0aRCRD'
response = session.get(rest_url, timeout=60)
print(f'REST status: {response.status_code}')
print(f'Content type: {response.headers.get("content-type", "unknown")}')
if response.status_code == 200:
    import json
    data = response.json()
    print(f'Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}')
else:
    print(f'Response: {response.text[:500]}')
