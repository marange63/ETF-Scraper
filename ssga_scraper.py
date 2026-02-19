from io import BytesIO
from typing import Optional

import pandas as pd
import requests

from etf_scraper import ETFScraper


class SSGAScraper(ETFScraper):
    """Scraper for State Street Global Advisors (SPDR) ETF holdings from ssga.com."""

    # URL pattern for holdings downloads
    HOLDINGS_URL_TEMPLATE = (
        "https://www.ssga.com/library-content/products/fund-data/etfs/us/"
        "holdings-daily-us-en-{ticker}.xlsx"
    )

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Known SPDR ETF tickers (not exhaustive, but covers major funds)
    # The scraper will attempt to fetch any ticker, this is just for get_supported_tickers()
    KNOWN_TICKERS = [
        # S&P Index ETFs
        "SPY", "SPLG", "SPYG", "SPYV", "SPMD", "SPMV", "SPYD",
        # Dow Jones
        "DIA",
        # Mid/Small Cap
        "MDY", "SLY",
        # Sector ETFs
        "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLRE",
        # International
        "CWI", "GWL", "GWX",
        # Fixed Income
        "BIL", "BWX", "FLRN", "JNK", "SJNK", "SPAB", "SPBO", "SPSB", "SPIB", "SPLB",
        "SPTL", "SPTS", "SPTI",
        # Commodities
        "GLD", "GLDM", "IAU",
        # Real Estate
        "XLRE", "RWR", "RWX",
        # Other
        "KBE", "KRE", "XAR", "XBI", "XHB", "XHE", "XHS", "XME", "XOP", "XPH",
        "XRT", "XSD", "XSW", "XTH", "XTL", "XTN",
    ]

    @property
    def provider_name(self) -> str:
        return "State Street (SPDR)"

    def get_supported_tickers(self) -> list[str]:
        """
        Return a list of known SPDR ETF ticker symbols.

        Note: This list may not be exhaustive. The scraper will attempt to fetch
        holdings for any ticker provided to get_holdings().
        """
        return sorted(set(self.KNOWN_TICKERS))

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for a SPDR ETF.

        Args:
            ticker: The ETF ticker symbol (e.g., "SPY", "XLF")
            as_of_date: Not supported for SSGA - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not found or data cannot be retrieved
            requests.RequestException: If the HTTP request fails
        """
        ticker = ticker.upper()

        url = self.HOLDINGS_URL_TEMPLATE.format(ticker=ticker.lower())

        response = requests.get(url, headers=self.HEADERS, timeout=60)

        if response.status_code == 404:
            raise ValueError(
                f"Ticker '{ticker}' not found. This may not be a SPDR ETF or "
                "holdings data may not be available."
            )

        response.raise_for_status()

        # Read Excel file from response content
        excel_data = BytesIO(response.content)

        # SSGA Excel files have metadata rows at the top, read without header first
        df_raw = pd.read_excel(excel_data, header=None, engine='openpyxl')

        # Find the header row (contains "Name" and "Weight" columns)
        header_row = 0
        for i, row in df_raw.iterrows():
            row_values = [str(v).strip() for v in row.values if pd.notna(v)]
            if 'Name' in row_values and 'Weight' in row_values:
                header_row = i
                break

        # Re-read with correct header row
        excel_data.seek(0)
        df = pd.read_excel(excel_data, header=header_row, engine='openpyxl')

        # Clean up column names
        df.columns = df.columns.str.strip()

        # Remove any completely empty rows
        df = df.dropna(how='all')

        # Remove footer/disclaimer rows - keep only rows with valid weight data
        weight_col = next((c for c in df.columns if 'weight' in c.lower()), None)
        if weight_col is None:
            raise ValueError(f"Could not find a weight column in holdings data for '{ticker}'")
        df = df[pd.to_numeric(df[weight_col], errors='coerce').notna()]

        # Rename columns and add ETF Ticker
        df = df.rename(columns={weight_col: 'Weight', 'Ticker': 'Holding'})
        df['ETF Ticker'] = ticker
        df = df[['ETF Ticker', 'Holding', 'Weight']]

        return df
