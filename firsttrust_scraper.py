from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

from etf_scraper import ETFScraper


class FirstTrustScraper(ETFScraper):
    """Scraper for First Trust ETF holdings from ftportfolios.com."""

    HOLDINGS_URL_TEMPLATE = (
        "https://www.ftportfolios.com/Retail/Etf/EtfHoldings.aspx?Ticker={ticker}"
    )

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    TIMEOUT = 60

    # Known First Trust ETF tickers (not exhaustive).
    # The scraper will attempt any ticker — this list is only for get_supported_tickers().
    KNOWN_TICKERS = [
        "AIRR", "CIBR", "CLOU", "FDN", "FPRO", "FTEC", "FTXL",
        "LEGR", "LMBS", "MILN", "SKYY", "WNDY",
    ]

    @property
    def provider_name(self) -> str:
        return "First Trust"

    def get_supported_tickers(self) -> list[str]:
        return sorted(self.KNOWN_TICKERS)

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for a First Trust ETF.

        Args:
            ticker: The ETF ticker symbol (e.g., "CIBR", "SKYY")
            as_of_date: Not supported - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If holdings data cannot be found or parsed
            requests.RequestException: If the HTTP request fails
        """
        ticker = ticker.upper()
        url = self.HOLDINGS_URL_TEMPLATE.format(ticker=ticker)

        response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)
        response.raise_for_status()

        # Parse the page and find the inner holdings table.
        # Use recursive=False so we only inspect direct children of each table,
        # avoiding false matches from deeply nested outer layout tables.
        soup = BeautifulSoup(response.text, 'html.parser')
        target_table = None
        for table in soup.find_all('table'):
            direct_rows = table.find_all('tr', recursive=False)
            if not direct_rows:
                continue
            header_cells = [td.get_text(strip=True) for td in direct_rows[0].find_all(['td', 'th'], recursive=False)]
            if 'Identifier' in header_cells and 'Weighting' in header_cells:
                target_table = table
                break

        if target_table is None:
            raise ValueError(
                f"Could not find holdings table for '{ticker}'. "
                "The ticker may not be a First Trust ETF."
            )

        # Extract headers and data rows (skip header row)
        direct_rows = target_table.find_all('tr', recursive=False)
        headers = [td.get_text(strip=True) for td in direct_rows[0].find_all(['td', 'th'], recursive=False)]
        rows = [
            [td.get_text(strip=True) for td in tr.find_all(['td', 'th'], recursive=False)]
            for tr in direct_rows[1:]
            if tr.find_all(['td', 'th'], recursive=False)
        ]
        holdings_table = pd.DataFrame(rows, columns=headers)

        df = holdings_table

        # Drop rows without a valid weighting (footers, cash, etc.)
        df['Weighting'] = (
            df['Weighting'].astype(str).str.replace('%', '', regex=False).str.strip()
        )
        df = df[pd.to_numeric(df['Weighting'], errors='coerce').notna()].copy()
        df['Weighting'] = df['Weighting'].astype(float)

        df = df.rename(columns={'Identifier': 'Holding', 'Weighting': 'Weight'})
        df['ETF Ticker'] = ticker
        return df[['ETF Ticker', 'Holding', 'Weight']]
