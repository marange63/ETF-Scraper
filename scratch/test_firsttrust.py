from main import get_etf_holdings

for ticker in ['CIBR', 'SKYY']:
    df = get_etf_holdings(ticker, 'firsttrust')
    print(f'{ticker}: {len(df)} holdings, total weight {df["Weight"].sum():.2f}%')
    print(df.head(5).to_string())
    print()
