import re
from io import StringIO
from typing import Optional

import pandas as pd
import requests

from etf_scraper import ETFScraper


class GlobalXScraper(ETFScraper):
    """Scraper for Global X ETF holdings from globalxetfs.com."""

    FUND_PAGE_URL = "https://www.globalxetfs.com/funds/{ticker}"
    HOLDINGS_LINK_PATTERN = re.compile(
        r'https://assets\.globalxetfs\.com/funds/holdings/[^"\'<>\s]+full-holdings[^"\'<>\s]*\.csv',
        re.IGNORECASE
    )

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    TIMEOUT = 60

    # Known Global X ETF tickers (not exhaustive).
    # The scraper will attempt any ticker — this list is only for get_supported_tickers().
    KNOWN_TICKERS = [
        "BOTZ", "CLOU", "DRIV", "FINX", "GNOM", "HERO",
        "LIT",  "MILN", "POTX", "SNSR", "SOCL", "XITK",
    ]

    @property
    def provider_name(self) -> str:
        return "Global X"

    def get_supported_tickers(self) -> list[str]:
        return sorted(self.KNOWN_TICKERS)

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for a Global X ETF.

        Fetches the fund page to find the dated CSV download link, then
        downloads and parses the CSV.

        Args:
            ticker: The ETF ticker symbol (e.g., "BOTZ", "CLOU")
            as_of_date: Not supported - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the fund page or holdings CSV cannot be found
            requests.RequestException: If an HTTP request fails
        """
        ticker = ticker.upper()

        # Step 1: fetch fund page and extract dated CSV URL
        fund_url = self.FUND_PAGE_URL.format(ticker=ticker)
        page = requests.get(fund_url, headers=self.HEADERS, timeout=self.TIMEOUT)

        if page.status_code == 404:
            raise ValueError(
                f"Fund page not found for '{ticker}'. "
                "The ticker may not be a Global X ETF."
            )
        page.raise_for_status()

        match = self.HOLDINGS_LINK_PATTERN.search(page.text)
        if match is None:
            raise ValueError(
                f"Could not find holdings CSV link for '{ticker}' on the Global X fund page."
            )
        csv_url = match.group(0)

        # Step 2: download the CSV
        response = requests.get(csv_url, headers=self.HEADERS, timeout=self.TIMEOUT)
        response.raise_for_status()

        # CSV has 2 metadata rows (fund name, date), then the header row
        df = pd.read_csv(StringIO(response.text), skiprows=2)
        df.columns = df.columns.str.strip()

        # Drop footer/disclaimer rows (non-numeric weight)
        weight_col = next((c for c in df.columns if 'net assets' in c.lower()), None)
        if weight_col is None:
            raise ValueError(f"Could not find weight column in holdings data for '{ticker}'")

        df = df[pd.to_numeric(df[weight_col], errors='coerce').notna()].copy()
        df[weight_col] = df[weight_col].astype(float)

        df = df.rename(columns={weight_col: 'Weight', 'Ticker': 'Holding'})
        df['ETF Ticker'] = ticker
        return df[['ETF Ticker', 'Holding', 'Weight']]
