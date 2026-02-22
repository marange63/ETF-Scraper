import warnings
from typing import Optional

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

from ishares_scraper import ISharesScraper
from ssga_scraper import SSGAScraper
from invesco_scraper import InvescoScraper
from vaneck_scraper import VanEckScraper
from firsttrust_scraper import FirstTrustScraper
from ark_scraper import ARKScraper
from globalx_scraper import GlobalXScraper


# Registry of supported issuers — stores instances so scrapers can cache state
SCRAPER_REGISTRY = {
    "ishares": ISharesScraper(),
    "ssga": SSGAScraper(),
    "invesco": InvescoScraper(),
    "vaneck": VanEckScraper(),
    "firsttrust": FirstTrustScraper(),
    "ark": ARKScraper(),
    "globalx": GlobalXScraper(),
}


def get_portfolio_holdings(csv_path: str = "ETF-Portfolio.csv") -> pd.DataFrame:
    """
    Read ETF portfolio from CSV and return consolidated holdings.

    Args:
        csv_path: Path to CSV file with columns "ETF Ticker" and "Provider Name"

    Returns:
        Consolidated DataFrame with all holdings (skips failed ETFs with warning)
    """
    portfolio = pd.read_csv(csv_path)

    holdings = []
    for _, row in portfolio.iterrows():
        try:
            df = get_etf_holdings(row["ETF Ticker"], row["Provider Name"])
            total_weight = df["Weight"].sum()

            # Add placeholder for missing holdings to force sum to 100%
            if total_weight < 100:
                remaining_weight = 100 - total_weight
                placeholder = pd.DataFrame({
                    "ETF Ticker": [row["ETF Ticker"]],
                    "Holding": ["OTHER"],
                    "Weight": [remaining_weight]
                })
                df = pd.concat([df, placeholder], ignore_index=True)
                total_weight = 100

            num_holdings = len(df)
            top10_weight = df.head(10)["Weight"].sum()
            top_holding = df.iloc[0]
            print(f"{row['ETF Ticker']:6} | Holdings: {num_holdings:4} | Total Weight: {total_weight:6.2f}% | Top 10 Weight: {top10_weight:5.2f}% | Top Holding: {top_holding['Holding']} ({top_holding['Weight']:.2f}%)")
            holdings.append(df)
        except Exception as e:
            print(f"Warning: Failed to fetch {row['ETF Ticker']}: {e}")

    return pd.concat(holdings, ignore_index=True) if holdings else pd.DataFrame()


def get_etf_holdings(ticker: str, issuer: str, as_of_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve ETF holdings for a given ticker and issuer.

    Args:
        ticker: The ETF ticker symbol (e.g., "SPY", "IVV")
        issuer: The ETF issuer name ("ishares", "ssga", or "invesco")
        as_of_date: Optional date string in YYYY-MM-DD format (iShares only)

    Returns:
        pandas DataFrame containing the holdings data

    Raises:
        ValueError: If the issuer is not supported
        ValueError: If the ticker is not found
        requests.RequestException: If the HTTP request fails
    """
    issuer = issuer.lower()

    if issuer not in SCRAPER_REGISTRY:
        supported = ", ".join(SCRAPER_REGISTRY.keys())
        raise ValueError(f"Unsupported issuer '{issuer}'. Supported issuers: {supported}")

    return SCRAPER_REGISTRY[issuer].get_holdings(ticker, as_of_date)


def show_holdings_inspector(df: pd.DataFrame) -> None:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("ETF Holdings Inspector")
    root.geometry("900x550")

    tickers = sorted(df["ETF Ticker"].unique().tolist())

    # ── Left panel: label + combobox ──────────────────────────────────────
    left = tk.Frame(root, width=180)
    left.pack(side=tk.LEFT, fill=tk.Y, padx=(12, 6), pady=12)
    left.pack_propagate(False)

    tk.Label(left, text="ETF Ticker", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 4))
    selected = tk.StringVar(value=tickers[0] if tickers else "")
    combo = ttk.Combobox(left, textvariable=selected, values=tickers, state="readonly", width=14)
    combo.pack(fill=tk.X)

    # ── Right panel: treeview + scrollbar ────────────────────────────────
    right = tk.Frame(root)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 12), pady=12)

    tree = ttk.Treeview(right, columns=("Holding", "Weight"), show="headings")
    tree.heading("Holding", text="Holding")
    tree.heading("Weight",  text="Weight (%)")
    tree.column("Holding", width=260, anchor=tk.W)
    tree.column("Weight",  width=100, anchor=tk.E)

    vsb = ttk.Scrollbar(right, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    # ── Exit button — bottom-right ────────────────────────────────────────
    btn_bar = tk.Frame(root)
    btn_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 10))
    tk.Button(btn_bar, text="Exit", width=10, command=root.destroy).pack(side=tk.RIGHT)

    # ── Populate table whenever selection changes ─────────────────────────
    def _refresh(*_):
        tree.delete(*tree.get_children())
        for _, row in df[df["ETF Ticker"] == selected.get()].iterrows():
            tree.insert("", tk.END, values=(row["Holding"], f"{row['Weight']:.4f}"))

    selected.trace_add("write", _refresh)
    _refresh()          # initial populate

    root.mainloop()     # blocks until window is closed


if __name__ == '__main__':
    # Example using the get_portfolio_holdings function
    print("=" * 60)
    print("Portfolio Holdings")
    print("=" * 60)

    try:
        holdings_df = get_portfolio_holdings()
        print(f"Retrieved {len(holdings_df)} total holdings")
        print(f"\nColumns: {', '.join(holdings_df.columns)}")
        print(f"\nETFs in portfolio: {holdings_df['ETF Ticker'].unique().tolist()}")
        print(f"\nTop 10 holdings:")
        print(holdings_df.head(10))

        holdings_df["Holding"] = holdings_df["Holding"].astype(str)
        output_path = "holdings_output.csv"
        holdings_df.to_csv(output_path, index=False)
        print(f"\nHoldings saved to {output_path}")
        show_holdings_inspector(holdings_df)
    except Exception as e:
        print(f"Error retrieving portfolio holdings: {e}")
