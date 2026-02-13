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

### Scraper Registry

`SCRAPER_REGISTRY` in `main.py`: `{"ishares": ISharesScraper, "ssga": SSGAScraper, "invesco": InvescoScraper}`

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

## Adding New Issuers

1. Create a scraper class inheriting from `ETFScraper`
2. Implement `provider_name`, `get_holdings()`, and `get_supported_tickers()`
3. Add to `SCRAPER_REGISTRY` in `main.py`

## Network

Timeouts: 60-90s with automatic retry. iShares caches ETF index at class level after first fetch.
