from main import get_etf_holdings

for ticker in ['ARKK', 'ARKQ']:
    df = get_etf_holdings(ticker, 'ark')
    print(f'{ticker}: {len(df)} holdings, total weight {df["Weight"].sum():.2f}%')
    print(df.head(5).to_string())
    print()
