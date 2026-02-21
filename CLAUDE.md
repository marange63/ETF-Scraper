# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETF-Comp-Scrape scrapes ETF holdings data from fund issuers (iShares, State Street SPDR, Invesco, VanEck) and returns pandas DataFrames.

## Setup

```bash
# Install dependencies
conda install -n ETF-Comp-Scrape requests pandas beautifulsoup4 openpyxl yfinance -y

# Run
conda activate ETF-Comp-Scrape
python main.py
```

IDE: PyCharm with `ETF-Comp-Scrape` conda interpreter.

## Architecture

| File | Purpose |
|------|---------|
| `main.py` | Entry point with `get_etf_holdings()`, `get_portfolio_holdings()`, and `SCRAPER_REGISTRY` |
| `etf_scraper.py` | Abstract base class `ETFScraper` |
| `ishares_scraper.py` | `ISharesScraper` - scrapes ishares.com (CSV download) |
| `ssga_scraper.py` | `SSGAScraper` - scrapes ssga.com (Excel download) |
| `invesco_scraper.py` | `InvescoScraper` - uses yfinance (top 10 holdings only) |
| `vaneck_scraper.py` | `VanEckScraper` - scrapes vaneck.com (CSV or Excel download) |
| `scratch/test_invesco.py` | Ad-hoc exploration/debug script (not a test framework) |

### ETFScraper Base Class

Abstract methods (must implement):
- `provider_name` - property returning issuer name
- `get_holdings(ticker, as_of_date)` - returns DataFrame with columns: `ETF Ticker`, `Holding`, `Weight`
- `get_supported_tickers()` - returns list of tickers

Inherited methods:
- `is_supported(ticker)` - checks ticker support
- `display_top_holdings(ticker, n)` - prints top N holdings

### Scraper Limitations

| Scraper | `as_of_date` support | Holdings coverage |
|---------|---------------------|-------------------|
| iShares | Yes | Full |
| SSGA | No (ignored) | Full |
| Invesco | No (ignored) | Top 10 only (yfinance limitation) |
| VanEck | No (ignored) | Full |

### Scraper Registry

`SCRAPER_REGISTRY` in `main.py` stores **instances** (not classes): `{"ishares": ISharesScraper(), "ssga": SSGAScraper(), "invesco": InvescoScraper(), "vaneck": VanEckScraper()}`. This allows scrapers to cache state across calls (iShares caches its ETF index at the class level after the first fetch).

### Scraper Implementation Details

**ISharesScraper**: Fetches the product listing page (`/us/products/etf-investments`) once at class level, parses anchor tags to build a `{ticker: {product_id, slug}}` index, then downloads holdings as CSV from `/{product_id}/{slug}/1467271812596.ajax?fileType=csv`. The CSV has metadata rows at the top — the scraper skips to the row containing `Ticker`, `Name`, and `Weight` headers, and stops at empty lines or disclaimer text. Timeouts: 90s for the product listing page, 30s for the CSV download.

**SSGAScraper**: Downloads directly from a predictable URL: `https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-{ticker_lowercase}.xlsx`. The Excel file has metadata rows at the top; the scraper finds the header row by scanning for `Name` and `Weight` values, then filters out footer rows using `pd.to_numeric`. `KNOWN_TICKERS` is a static list used only by `get_supported_tickers()` — the scraper attempts any ticker.

**InvescoScraper**: Uses `yf.Ticker(ticker).funds_data.top_holdings`. Weights come back as decimals (0–1) and are multiplied by 100. `KNOWN_TICKERS` is static; any ticker can be attempted.

**VanEckScraper**: Downloads from `https://www.vaneck.com/us/en/investments/{slug}/downloads/holdings/`. The slug (e.g., `uranium-nuclear-energy-etf-nlr`) is not derivable from the ticker alone, so it must be added to `TICKER_SLUG_MAP` in `vaneck_scraper.py`. The response is parsed as Excel or CSV based on the `Content-Type` header. Footer rows are removed using `pd.to_numeric`. Prefers `Ticker` column for the holding identifier, falling back to `Name`.

### Portfolio Batch Processing

`get_portfolio_holdings()` reads `ETF-Portfolio.csv` (columns: `ETF Ticker`, `Provider Name`). If total weight < 100%, it inserts a placeholder row with `Holding = "OTHER"` to pad to 100%. Failed ETFs are skipped with a warning. Output is written to `holdings_output.csv`.

**Note**: `*.csv` files are gitignored. `ETF-Portfolio.csv` must be created locally — see the example format below.

## Usage

```python
from main import get_etf_holdings, get_portfolio_holdings

# Single ETF
df = get_etf_holdings("IVV", "ishares")
df = get_etf_holdings("IVV", "ishares", as_of_date="2024-01-31")  # iShares only
df = get_etf_holdings("SPY", "ssga")
df = get_etf_holdings("QQQ", "invesco")
df = get_etf_holdings("NLR", "vaneck")

# Batch from CSV (requires ETF-Portfolio.csv with "ETF Ticker" and "Provider Name" columns)
df = get_portfolio_holdings("ETF-Portfolio.csv")
```

Example `ETF-Portfolio.csv`:
```
ETF Ticker,Provider Name
IVV,ishares
SPY,ssga
QQQ,invesco
NLR,vaneck
```

## Adding New Issuers

1. Create a scraper class inheriting from `ETFScraper`
2. Implement `provider_name`, `get_holdings()`, and `get_supported_tickers()`
3. Add an instance to `SCRAPER_REGISTRY` in `main.py`

## Adding New VanEck Tickers

VanEck tickers require a manual slug mapping. Find the slug in the VanEck product URL (`vaneck.com/us/en/investments/{slug}/`) and add `"TICKER": "slug"` to `TICKER_SLUG_MAP` in `vaneck_scraper.py`.

## Network

Timeouts: 60–90s for initial page fetches, 30s for data downloads. iShares uses a session with automatic retry (3 retries, backoff factor 1, on 429/5xx) and caches the ETF index at class level after the first fetch. SSGA, Invesco, and VanEck do not retry.
