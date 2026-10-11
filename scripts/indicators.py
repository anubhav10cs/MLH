"""Compute technical indicators and risk metrics from cleaned price data."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def _number_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None


def calculate_indicators(frame: pd.DataFrame) -> dict[str, Any]:
    """Return the latest technical indicators and full-period risk statistics."""
    if "close" not in frame.columns:
        raise ValueError("Cleaned data must contain a close column.")
    close = pd.to_numeric(frame["close"], errors="coerce").astype(float)
    close = close.where(np.isfinite(close) & (close > 0)).dropna()
    if close.empty:
        raise ValueError("No valid positive close prices are available.")

    returns = close.pct_change(fill_method=None).dropna()
    equity = close / close.iloc[0]
    drawdown = close / close.cummax() - 1.0
    daily_std = float(returns.std(ddof=1)) if len(returns) > 1 else float("nan")
    cumulative_return = float(equity.iloc[-1] - 1.0)
    annualized_return = (
        float((close.iloc[-1] / close.iloc[0]) ** (TRADING_DAYS / len(returns)) - 1)
        if len(returns) and close.iloc[-1] > 0
        else float("nan")
    )
    annualized_volatility = daily_std * math.sqrt(TRADING_DAYS)
    sharpe = (
        float(returns.mean() / daily_std * math.sqrt(TRADING_DAYS))
        if math.isfinite(daily_std) and daily_std > 0
        else float("nan")
    )

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    average_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    relative_strength = average_gain / average_loss
    rsi = 100 - 100 / (1 + relative_strength)
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50)

    ema_12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema_26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False, min_periods=9).mean()

    dates = frame.loc[close.index, "date"] if "date" in frame.columns else None
    start = str(dates.iloc[0]) if dates is not None else None
    end = str(dates.iloc[-1]) if dates is not None else None

    def last(series: pd.Series) -> float | None:
        values = series.dropna()
        return _number_or_none(values.iloc[-1]) if not values.empty else None

    return {
        "rows": int(len(close)),
        "start_date": start,
        "end_date": end,
        "latest_close": float(close.iloc[-1]),
        "indicators": {
            "sma_20": last(close.rolling(20, min_periods=20).mean()),
            "sma_50": last(close.rolling(50, min_periods=50).mean()),
            "ema_20": last(close.ewm(span=20, adjust=False, min_periods=20).mean()),
            "rsi_14": last(rsi),
            "macd": last(macd_line),
            "macd_signal": last(macd_signal),
            "macd_histogram": last(macd_line - macd_signal),
            "daily_return": _number_or_none(float(returns.iloc[-1]))
            if len(returns)
            else None,
        },
        "risk": {
            "cumulative_return": _number_or_none(cumulative_return),
            "annualized_return": _number_or_none(annualized_return),
            "annualized_volatility": _number_or_none(annualized_volatility),
            "sharpe_ratio_rf_0": _number_or_none(sharpe),
            "max_drawdown": _number_or_none(float(drawdown.min())),
        },
    }


def write_metrics(
    frame: pd.DataFrame, output_path: str | Path = "metrics.json"
) -> dict[str, Any]:
    metrics = calculate_indicators(frame)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(metrics, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="clean.csv", help="Clean CSV path.")
    parser.add_argument("--output", default="metrics.json", help="JSON output path.")
    args = parser.parse_args()
    try:
        frame = pd.read_csv(args.input)
        metrics = write_metrics(frame, args.output)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.error(str(error))
    print(f"Computed indicators for {metrics['rows']} rows; wrote {args.output}.")


if __name__ == "__main__":
    main()
