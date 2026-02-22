from io import StringIO
from typing import Optional

import pandas as pd
import requests

from etf_scraper import ETFScraper


class PacerScraper(ETFScraper):
    """Scraper for Pacer ETF holdings from paceretfs.com."""

    HOLDINGS_URL_TEMPLATE = (
        "https://www.paceretfs.com/usbank/live/fsb0.pacer.x330.{ticker}_Holdings.csv"
    )

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    TIMEOUT = 60

    # Known Pacer ETF tickers — scraper will attempt any ticker, this is for get_supported_tickers()
    KNOWN_TICKERS = [
        "BUFD", "BUFR", "BUFT", "BUFU",       # Buffer ETFs
        "CALF",                                 # US Small Cap Cash Cows
        "COWZ",                                 # US Cash Cows 100
        "EVNT",                                 # Swan Hedged Equity US Large Cap
        "ICOW",                                 # Developed Markets International Cash Cows 100
        "IDOG",                                 # ALPS International Sector Dividend Dogs
        "LRGF",                                 # Lunt Large Cap Multi-Factor Alternator
        "PAUG", "PFEB", "PJAN", "PJUL",        # Buffer ETFs (monthly series)
        "PMAR", "PMAY", "PNOV", "POCT",
        "PSEP", "PAPR", "PDEC", "PJUN",
        "QARP",                                 # CSOP ETF
        "SRVR",                                 # Data & Infrastructure Real Estate
        "TRFK",                                 # Funds Trust
        "VIRS",                                 # BioThreat Strategy
    ]

    @property
    def provider_name(self) -> str:
        return "Pacer ETFs"

    def get_supported_tickers(self) -> list[str]:
        return sorted(set(self.KNOWN_TICKERS))

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for a Pacer ETF.

        Args:
            ticker: The ETF ticker symbol (e.g., "SRVR", "COWZ")
            as_of_date: Not supported - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not found or data cannot be parsed
            requests.RequestException: If the HTTP request fails
        """
        ticker = ticker.upper()

        url = self.HOLDINGS_URL_TEMPLATE.format(ticker=ticker)
        response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT)

        if response.status_code == 404:
            raise ValueError(
                f"Ticker '{ticker}' not found. This may not be a Pacer ETF or "
                "holdings data may not be available."
            )
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()

        # Strip % and convert weight to float
        df['Weightings'] = (
            df['Weightings'].astype(str).str.replace('%', '', regex=False).str.strip()
        )
        df = df[pd.to_numeric(df['Weightings'], errors='coerce').notna()].copy()
        df['Weightings'] = df['Weightings'].astype(float)

        df = df.rename(columns={'StockTicker': 'Holding', 'Weightings': 'Weight'})
        df['ETF Ticker'] = ticker
        return df[['ETF Ticker', 'Holding', 'Weight']]
