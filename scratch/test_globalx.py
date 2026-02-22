from main import get_etf_holdings

df = get_etf_holdings('BOTZ', 'globalx')
print(f'BOTZ: {len(df)} holdings, total weight {df["Weight"].sum():.2f}%')
print(df.head(5).to_string())
