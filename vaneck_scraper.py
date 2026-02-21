from io import BytesIO, StringIO
from typing import Optional

import pandas as pd
import requests

from etf_scraper import ETFScraper


class VanEckScraper(ETFScraper):
    """Scraper for VanEck ETF holdings from vaneck.com."""

    # URL pattern: vaneck.com/us/en/investments/{slug}/downloads/holdings/
    HOLDINGS_URL_TEMPLATE = (
        "https://www.vaneck.com/us/en/investments/{slug}/downloads/holdings/"
    )

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    TIMEOUT = 60

    # Maps ticker -> URL slug found in the VanEck product URL.
    # To add a ticker: find the slug at vaneck.com/us/en/investments/{slug}/
    # and add it here.
    TICKER_SLUG_MAP = {
        "ANGL": "fallen-angel-high-yield-bond-etf-angl",
        "GDX": "gold-miners-etf-gdx",
        "GDXJ": "junior-gold-miners-etf-gdxj",
        "HYD": "high-yield-muni-etf-hyd",
        "ITM": "intermediate-muni-etf-itm",
        "MOAT": "morningstar-wide-moat-etf-moat",
        "NLR": "uranium-nuclear-energy-etf-nlr",
        "REMX": "rare-earth-strategic-metals-etf-remx",
        "SMH": "semiconductor-etf-smh",
        "VNM": "vietnam-etf-vnm",
    }

    @property
    def provider_name(self) -> str:
        return "VanEck"

    def get_supported_tickers(self) -> list[str]:
        return sorted(self.TICKER_SLUG_MAP.keys())

    def get_holdings(self, ticker: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
        """
        Retrieve holdings data for a VanEck ETF.

        Args:
            ticker: The ETF ticker symbol (e.g., "NLR", "SMH")
            as_of_date: Not supported - only current holdings available.
                        This parameter is ignored.

        Returns:
            pandas DataFrame containing the holdings data with columns:
            - ETF Ticker, Holding, Weight

        Raises:
            ValueError: If the ticker is not in TICKER_SLUG_MAP or data cannot be parsed
            requests.RequestException: If the HTTP request fails
        """
        ticker = ticker.upper()

        if ticker not in self.TICKER_SLUG_MAP:
            raise ValueError(
                f"Ticker '{ticker}' not found in VanEck scraper. "
                f"Supported tickers: {', '.join(self.get_supported_tickers())}. "
                "To add support for a new ticker, add its slug to TICKER_SLUG_MAP in vaneck_scraper.py."
            )

        slug = self.TICKER_SLUG_MAP[ticker]
        url = self.HOLDINGS_URL_TEMPLATE.format(slug=slug)

        response = requests.get(url, headers=self.HEADERS, timeout=self.TIMEOUT, allow_redirects=True)

        if response.status_code == 404:
            raise ValueError(
                f"Holdings data not found for '{ticker}'. "
                f"The slug '{slug}' may be incorrect — verify at vaneck.com/us/en/investments/{slug}/"
            )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "spreadsheetml" in content_type or "excel" in content_type:
            df = self._parse_excel(response.content, ticker)
        else:
            df = self._parse_csv(response.text, ticker)

        return df

    def _parse_excel(self, content: bytes, ticker: str) -> pd.DataFrame:
        excel_data = BytesIO(content)
        df_raw = pd.read_excel(excel_data, header=None, engine='openpyxl')

        header_row = 0
        for i, row in df_raw.iterrows():
            row_values = [str(v).strip() for v in row.values if pd.notna(v)]
            has_holding = 'Ticker' in row_values or 'Name' in row_values
            has_weight = any('weight' in v.lower() or 'net assets' in v.lower() for v in row_values)
            if has_holding and has_weight:
                header_row = i
                break

        excel_data.seek(0)
        df = pd.read_excel(excel_data, header=header_row, engine='openpyxl')
        return self._normalise(df, ticker)

    def _parse_csv(self, text: str, ticker: str) -> pd.DataFrame:
        lines = text.split('\n')

        data_start = 0
        for i, line in enumerate(lines):
            if ('Ticker' in line or 'Name' in line) and 'Weight' in line:
                data_start = i
                break

        data_end = len(lines)
        for i in range(data_start + 1, len(lines)):
            if not lines[i].strip():
                data_end = i
                break

        df = pd.read_csv(StringIO('\n'.join(lines[data_start:data_end])))
        return self._normalise(df, ticker)

    def _normalise(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Rename columns to the standard ETF Ticker / Holding / Weight schema."""
        df.columns = df.columns.str.strip()
        df = df.dropna(how='all')

        weight_col = next(
            (c for c in df.columns if 'weight' in c.lower() or 'net assets' in c.lower()),
            None
        )
        if weight_col is None:
            raise ValueError(f"Could not find weight column in holdings data for '{ticker}'")

        # VanEck formats weights as "9.00%" strings — strip % and convert to float
        df[weight_col] = (
            df[weight_col].astype(str).str.replace('%', '', regex=False).str.strip()
        )

        # Drop footer/disclaimer rows
        df = df[pd.to_numeric(df[weight_col], errors='coerce').notna()].copy()
        df[weight_col] = df[weight_col].astype(float)

        # Prefer 'Ticker' column for the holding identifier; fall back to 'Name'
        holding_col = next((c for c in df.columns if c.strip().lower() == 'ticker'), None)
        if holding_col is None:
            holding_col = next((c for c in df.columns if 'name' in c.lower()), None)
        if holding_col is None:
            raise ValueError(f"Could not find ticker/name column in holdings data for '{ticker}'")

        df = df.rename(columns={weight_col: 'Weight', holding_col: 'Holding'})
        df['ETF Ticker'] = ticker
        return df[['ETF Ticker', 'Holding', 'Weight']]
