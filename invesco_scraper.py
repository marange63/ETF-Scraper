from typing import Optional

import pandas as pd
import yfinance as yf

from etf_scraper import ETFScraper


class InvescoScraper(ETFScraper):
    """Scraper for Invesco ETF holdings using Yahoo Finance (yfinance).

    Note: Yahoo Finance only provides top 10 holdings, not the full list.
    """

    # Known Invesco ETF tickers (not exhaustive)
    KNOWN_TICKERS = [
        # NASDAQ / Tech
        "QQQ", "QQQM", "QQQJ", "QQQA", "QQQN",
        # S&P 500
        "RSP", "SPGP",
        # Equal Weight Sector
        "RCD", "RGI", "RTM", "RYE", "RYF", "RYH", "RYT", "RYU",
        # Dividend
        "PEY", "PFM", "PKW", "SPHD",
        # Factor ETFs
        "PRF", "PRFZ", "DWAS", "OMFL",
        # Fixed Income
        "BSCM", "BSCN", "BSCO", "BSCP", "BSCQ", "BSCR", "BSCS", "BSCT", "BSCU",
        # International
        "PDN", "PXH", "PIZ", "PIE",
        # Commodities
        "DBC", "DBB", "DBO", "DBP", "DBS",
        # Other
        "PHO", "PBW", "PNQI", "CGW",
    ]

    @property
    def provider_name(self) -> str:
        return "Invesco"

    def get_supported_tickers(self) -> list[str]:
        """
        Return a list of known Invesco ETF ticker symbols.

        Note: This list may not be exhaustive. The scraper will attempt to fetch
        holdings for any ticker provided to get_holdings().
        """
        return sorted(set(self.KNOWN_TICKERS))

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for an Invesco ETF via Yahoo Finance.

        Note: Yahoo Finance only provides top 10 holdings, not the full list.

        Args:
            ticker: The ETF ticker symbol (e.g., "QQQ", "RSP")
            as_of_date: Not supported - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not found or data cannot be retrieved
        """
        ticker = ticker.upper()

        etf = yf.Ticker(ticker)

        try:
            holdings = etf.funds_data.top_holdings
        except Exception as e:
            raise ValueError(f"Failed to fetch holdings for {ticker}: {e}")

        if holdings is None or holdings.empty:
            raise ValueError(f"No holdings data available for {ticker}")

        # Reset index to get symbol as a column
        df = holdings.reset_index()

        # Rename columns to match expected format
        # yfinance returns: Symbol (index), Name, Holding Percent
        df = df.rename(columns={"Symbol": "Holding", "Holding Percent": "Weight"})

        # Convert weight from decimal to percentage
        df["Weight"] = df["Weight"] * 100

        df["ETF Ticker"] = ticker

        # Select and order columns
        df = df[["ETF Ticker", "Holding", "Weight"]]

        return df
