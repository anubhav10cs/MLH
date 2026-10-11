"""Read and normalize CSV or Parquet OHLCV/price data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ALIASES = {
    "date": ("date", "datetime", "timestamp", "time", "tradingdate"),
    "open": ("open", "openprice", "openingprice"),
    "high": ("high", "highprice"),
    "low": ("low", "lowprice"),
    "close": (
        "close",
        "closeprice",
        "closingprice",
        "adjclose",
        "adjustedclose",
        "ltp",
        "lasttradedprice",
        "price",
        "settle",
        "settlement",
    ),
    "volume": ("volume", "vol", "tradedvolume", "qty", "quantity"),
}


def _normalize_column(name: object) -> str:
    return "".join(character.lower() for character in str(name) if character.isalnum())


def _read_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        try:
            return pd.read_parquet(path)
        except ImportError as error:
            raise RuntimeError(
                "Reading Parquet requires a pandas Parquet engine; install pyarrow "
                "or fastparquet in this environment."
            ) from error
    raise ValueError("Input must have a .csv, .parquet, or .pq extension.")


def load_data(
    input_path: str | Path, output_path: str | Path = "clean.csv"
) -> pd.DataFrame:
    """Load, normalize, clean, optionally sort, and write price data."""
    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(f"Input file not found: {source}")
    frame = _read_source(source)
    if frame.empty and len(frame.columns) == 0:
        raise ValueError("Input data has no columns.")

    normalized = {_normalize_column(column): column for column in frame.columns}
    rename: dict[object, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            source_column = normalized.get(alias)
            if source_column is not None:
                rename[source_column] = canonical
                break

    if "close" not in rename.values():
        raise ValueError(
            "Could not find a close column. Accepted names include close, "
            "adj close, adjusted close, ltp, and price."
        )

    frame = frame.rename(columns=rename)
    frame = frame.loc[:, ~frame.columns.duplicated()].copy()
    for column in ("open", "high", "low", "close", "volume"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce", utc=True)
        frame = frame.dropna(subset=["date"]).sort_values("date", kind="stable")
        frame["date"] = frame["date"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    close_values = frame["close"].to_numpy(dtype=float)
    valid_close = np.isfinite(close_values) & (close_values > 0)
    dropped = int((~valid_close).sum())
    frame = frame.loc[valid_close].reset_index(drop=True)
    if dropped:
        print(
            f"Warning: dropped {dropped} row(s) with missing, non-numeric, "
            "non-finite, or non-positive close values.",
            file=sys.stderr,
        )
    if len(frame) < 30:
        print(
            f"Warning: only {len(frame)} valid rows; indicator and backtest "
            "results may be unstable or unavailable.",
            file=sys.stderr,
        )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Input CSV or Parquet file.")
    parser.add_argument("--output", default="clean.csv", help="Clean CSV path.")
    args = parser.parse_args()
    try:
        frame = load_data(args.path, args.output)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    print(f"Loaded {len(frame)} rows; wrote {args.output}.")


if __name__ == "__main__":
    main()
