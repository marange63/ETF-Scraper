from io import StringIO
from typing import Optional

import pandas as pd
import requests

from etf_scraper import ETFScraper


class ARKScraper(ETFScraper):
    """Scraper for ARK Investment Management ETF holdings from assets.ark-funds.com."""

    BASE_URL = "https://assets.ark-funds.com/fund-documents/funds-etf-csv/{filename}.csv"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    TIMEOUT = 60

    # Maps ticker -> CSV filename (without .csv extension).
    # To add a ticker: find the filename at ark-funds.com/download-fund-materials
    # and add it here.
    TICKER_FILENAME_MAP = {
        "ARKF": "ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS",
        "ARKG": "ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS",
        "ARKK": "ARK_INNOVATION_ETF_ARKK_HOLDINGS",
        "ARKQ": "ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS",
        "ARKW": "ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS",
        "ARKX": "ARK_SPACE_EXPLORATION_&_INNOVATION_ETF_ARKX_HOLDINGS",
    }

    @property
    def provider_name(self) -> str:
        return "ARK Investment Management"

    def get_supported_tickers(self) -> list[str]:
        return sorted(self.TICKER_FILENAME_MAP.keys())

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for an ARK ETF.

        Args:
            ticker: The ETF ticker symbol (e.g., "ARKK", "ARKQ")
            as_of_date: Not supported - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not in TICKER_FILENAME_MAP or data cannot be parsed
            requests.RequestException: If the HTTP request fails
        """
        ticker = ticker.upper()

        if ticker not in self.TICKER_FILENAME_MAP:
            raise ValueError(
                f"Ticker '{ticker}' not found in ARK scraper. "
                f"Supported tickers: {', '.join(self.get_supported_tickers())}. "
                "To add support for a new ticker, add its CSV filename to TICKER_FILENAME_MAP in ark_scraper.py."
            )

        filename = self.TICKER_FILENAME_MAP[ticker]
        url = self.BASE_URL.format(filename=filename)

        response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)

        if response.status_code == 404:
            raise ValueError(
                f"Holdings CSV not found for '{ticker}'. "
                f"The filename '{filename}' may be incorrect — verify at ark-funds.com/download-fund-materials"
            )
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()

        # Strip % and convert weight to float
        df['weight (%)'] = (
            df['weight (%)'].astype(str).str.replace('%', '', regex=False).str.strip()
        )
        df = df[pd.to_numeric(df['weight (%)'], errors='coerce').notna()].copy()
        df['weight (%)'] = df['weight (%)'].astype(float)

        df = df.rename(columns={'ticker': 'Holding', 'weight (%)': 'Weight'})
        df['ETF Ticker'] = ticker
        return df[['ETF Ticker', 'Holding', 'Weight']]
