# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETF-Comp-Scrape scrapes ETF holdings data from fund issuers (iShares, State Street SPDR, Invesco) and returns pandas DataFrames.

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
| `test_invesco.py` | Ad-hoc exploration/debug script (not a test framework) |

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

Note: `get_etf_holdings()` in `main.py` does not currently pass `as_of_date` to scrapers — it calls `scraper.get_holdings(ticker)` only.

### Scraper Registry

`SCRAPER_REGISTRY` in `main.py`: `{"ishares": ISharesScraper, "ssga": SSGAScraper, "invesco": InvescoScraper}`

### Scraper Implementation Details

**ISharesScraper**: Fetches the product listing page (`/us/products/etf-investments`) once at class level, parses anchor tags to build a `{ticker: {product_id, slug}}` index, then downloads holdings as CSV from `/{product_id}/{slug}/1467271812596.ajax?fileType=csv`. The CSV has metadata rows at the top — the scraper skips to the row containing `Ticker`, `Name`, and `Weight` headers, and stops at empty lines or disclaimer text.

**SSGAScraper**: Downloads directly from a predictable URL: `https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-{ticker_lowercase}.xlsx`. The Excel file has metadata rows at the top; the scraper finds the header row by scanning for `Name` and `Weight` values, then filters out footer rows using `pd.to_numeric`. `KNOWN_TICKERS` is a static list used only by `get_supported_tickers()` — the scraper attempts any ticker.

**InvescoScraper**: Uses `yf.Ticker(ticker).funds_data.top_holdings`. Weights come back as decimals (0–1) and are multiplied by 100. `KNOWN_TICKERS` is static; any ticker can be attempted.

### Portfolio Batch Processing

`get_portfolio_holdings()` reads `ETF-Portfolio.csv` (columns: `ETF Ticker`, `Provider Name`). If total weight < 100%, it inserts a placeholder row with the ETF ticker as both `ETF Ticker` and `Holding` to pad to 100%. Output is written to `holdings_output.csv`.

**Note**: `*.csv` files are gitignored. `ETF-Portfolio.csv` must be created locally — see the example format below.

## Usage

```python
from main import get_etf_holdings, get_portfolio_holdings

# Single ETF
df = get_etf_holdings("IVV", "ishares")
df = get_etf_holdings("SPY", "ssga")
df = get_etf_holdings("QQQ", "invesco")

# Batch from CSV (requires ETF-Portfolio.csv with "ETF Ticker" and "Provider Name" columns)
df = get_portfolio_holdings("ETF-Portfolio.csv")
```

Example `ETF-Portfolio.csv`:
```
ETF Ticker,Provider Name
IVV,ishares
SPY,ssga
QQQ,invesco
```

## Adding New Issuers

1. Create a scraper class inheriting from `ETFScraper`
2. Implement `provider_name`, `get_holdings()`, and `get_supported_tickers()`
3. Add to `SCRAPER_REGISTRY` in `main.py`

## Network

Timeouts: 60–90s. iShares uses a session with automatic retry (3 retries, backoff, on 429/5xx) and caches the ETF index at class level after the first fetch. SSGA and Invesco do not retry.
