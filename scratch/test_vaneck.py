from main import get_etf_holdings

df = get_etf_holdings('NLR', 'vaneck')
print(f'Columns: {df.columns.tolist()}')
print(f'Rows: {len(df)}')
print(f'Total weight: {df["Weight"].sum():.2f}%')
print()
print(df.head(10).to_string())
