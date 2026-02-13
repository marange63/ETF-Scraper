import re
from io import StringIO
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from etf_scraper import ETFScraper


class ISharesScraper(ETFScraper):
    """Scraper for iShares ETF holdings from ishares.com."""

    # Class-level cache for ETF index (shared across all instances)
    _etf_index: dict[str, dict] = {}
    _index_loaded: bool = False
    _session: requests.Session = None

    PRODUCT_LISTING_URL = "https://www.ishares.com/us/products/etf-investments"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    TIMEOUT = 90  # seconds

    @classmethod
    def _get_session(cls) -> requests.Session:
        """Get or create a requests session with retry logic."""
        if cls._session is None:
            cls._session = requests.Session()
            cls._session.headers.update(cls.HEADERS)

            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            cls._session.mount("https://", adapter)
            cls._session.mount("http://", adapter)

        return cls._session

    @property
    def provider_name(self) -> str:
        return "iShares"

    def _fetch_etf_index(self) -> None:
        """Fetch the full ETF index from iShares product listing page."""
        if ISharesScraper._index_loaded:
            return

        session = self._get_session()
        response = session.get(
            self.PRODUCT_LISTING_URL,
            timeout=self.TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all product links matching pattern: /us/products/{id}/{slug}
        product_pattern = re.compile(r'/us/products/(\d+)/([a-z0-9-]+)')

        for link in soup.find_all('a', href=product_pattern):
            href = link.get('href', '')
            match = product_pattern.search(href)
            if match:
                product_id = match.group(1)
                slug = match.group(2)

                # The ticker is usually the link text for ticker links
                ticker_text = link.get_text(strip=True).upper()

                # Only store if it looks like a valid ticker (1-5 uppercase letters)
                if ticker_text and re.match(r'^[A-Z]{1,5}$', ticker_text):
                    ISharesScraper._etf_index[ticker_text] = {
                        "product_id": product_id,
                        "slug": slug
                    }

        ISharesScraper._index_loaded = True

    def _lookup_etf_info(self, ticker: str) -> dict:
        """
        Look up product info for a ticker, fetching the index if needed.

        Args:
            ticker: The ETF ticker symbol (uppercase)

        Returns:
            Dict with 'product_id' and 'slug' keys

        Raises:
            ValueError: If the ticker is not found
        """
        # Ensure index is loaded
        self._fetch_etf_index()

        if ticker not in ISharesScraper._etf_index:
            raise ValueError(
                f"Ticker '{ticker}' not found in iShares ETF index. "
                f"Found {len(ISharesScraper._etf_index)} ETFs. "
                "The ticker may not be an iShares ETF or may not be available in the US."
            )

        return ISharesScraper._etf_index[ticker]

    def get_supported_tickers(self) -> list[str]:
        self._fetch_etf_index()
        return sorted(ISharesScraper._etf_index.keys())

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for an iShares ETF.

        Args:
            ticker: The ETF ticker symbol (e.g., "IVV", "AGG")
            as_of_date: Optional date string in YYYY-MM-DD format. If None, returns latest holdings.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not found in the iShares ETF index
            requests.RequestException: If the HTTP request fails
        """
        ticker = ticker.upper()

        # Dynamically look up product info
        etf_info = self._lookup_etf_info(ticker)
        product_id = etf_info["product_id"]
        slug = etf_info["slug"]

        # Construct the holdings CSV URL
        base_url = f"https://www.ishares.com/us/products/{product_id}/{slug}/1467271812596.ajax"
        params = {
            "fileType": "csv",
            "fileName": f"{ticker}_holdings",
            "dataType": "fund",
        }

        if as_of_date:
            params["asOfDate"] = as_of_date

        response = requests.get(base_url, params=params, headers=self.HEADERS, timeout=30)
        response.raise_for_status()

        # The CSV has metadata rows at the top, find where the actual data starts
        lines = response.text.split('\n')

        # Find the header row (contains "Ticker" or "Name" as column headers)
        data_start = 0
        for i, line in enumerate(lines):
            if 'Ticker' in line and 'Name' in line and 'Weight' in line:
                data_start = i
                break

        # Find where data ends (empty line or footer)
        data_end = len(lines)
        for i in range(data_start + 1, len(lines)):
            # Stop at empty lines or disclaimer text
            if not lines[i].strip() or lines[i].startswith('"The content'):
                data_end = i
                break

        # Parse the CSV data
        csv_data = '\n'.join(lines[data_start:data_end])
        df = pd.read_csv(StringIO(csv_data))

        # Clean up column names
        df.columns = df.columns.str.strip()

        # Rename columns and add ETF Ticker
        df = df.rename(columns={'Weight (%)': 'Weight', 'Ticker': 'Holding'})
        df['ETF Ticker'] = ticker
        df = df[['ETF Ticker', 'Holding', 'Weight']]

        return df
