from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class ETFScraper(ABC):
    """Abstract base class for ETF holdings scrapers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the ETF provider (e.g., 'iShares', 'Vanguard')."""
        pass

    @abstractmethod
    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for an ETF.

        Args:
            ticker: The ETF ticker symbol
            as_of_date: Optional date string in YYYY-MM-DD format. If None, returns latest holdings.

        Returns:
            pandas DataFrame with columns: ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not supported
            requests.RequestException: If the HTTP request fails
        """
        pass

    @abstractmethod
    def get_supported_tickers(self) -> list[str]:
        """Return a list of supported ETF ticker symbols."""
        pass

    def is_supported(self, ticker: str) -> bool:
        """Check if a ticker is supported by this scraper."""
        return ticker.upper() in self.get_supported_tickers()

    def display_top_holdings(self, ticker: str, n: int = 10) -> None:
        """Display the top N holdings of an ETF."""
        df = self.get_holdings(ticker)

        print(f"\nTop {n} Holdings for {ticker} ({self.provider_name})")
        print("=" * 40)

        display_df = df.head(n)

        for _, row in display_df.iterrows():
            print(f"{row['Holding']:8} {row['Weight']:>10}")
