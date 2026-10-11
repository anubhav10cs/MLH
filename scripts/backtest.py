"""Backtest a shifted long-only SMA crossover against buy-and-hold."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _measure_strategy(
    close: pd.Series, position: pd.Series, trades: int
) -> dict[str, Any]:
    returns = close.pct_change(fill_method=None).fillna(0.0)
    strategy_returns = (position.astype(float) * returns).fillna(0.0)
    equity = (1.0 + strategy_returns).cumprod()
    total_return = float(equity.iloc[-1] - 1.0) if len(equity) else 0.0
    cagr = (
        float(equity.iloc[-1] ** (TRADING_DAYS / max(len(close) - 1, 1)) - 1.0)
        if len(close) > 1 and equity.iloc[-1] > 0
        else None
    )
    max_drawdown = (
        float((equity / equity.cummax() - 1.0).min()) if len(equity) else 0.0
    )

    # A trade is a contiguous held period; an open final position is marked to market.
    held = position.astype(bool).to_numpy()
    daily = returns.to_numpy(dtype=float)
    trade_returns: list[float] = []
    start: int | None = None
    for index, active in enumerate(held):
        if active and start is None:
            start = index
        if start is not None and (not active or index == len(held) - 1):
            stop = index if not active else index + 1
            trade_returns.append(float(np.prod(1.0 + daily[start:stop]) - 1.0))
            start = None
    win_rate = (
        float(sum(value > 0 for value in trade_returns) / len(trade_returns))
        if trade_returns
        else None
    )
    return {
        "total_return": total_return,
        "cagr": cagr if cagr is None or math.isfinite(cagr) else None,
        "max_drawdown": max_drawdown,
        "num_trades": int(trades),
        "trade_win_rate": win_rate,
    }


def run_backtest(
    frame: pd.DataFrame, fast: int = 20, slow: int = 50
) -> dict[str, Any]:
    """Return results for crossover and buy-and-hold strategies."""
    if fast < 1 or slow < 1:
        raise ValueError("fast and slow windows must be positive integers.")
    if fast >= slow:
        raise ValueError("--fast must be less than --slow.")
    if "close" not in frame.columns:
        raise ValueError("Cleaned data must contain a close column.")

    close = pd.to_numeric(frame["close"], errors="coerce").astype(float)
    valid = np.isfinite(close) & (close > 0)
    close = close.loc[valid].reset_index(drop=True)
    if close.empty:
        raise ValueError("No valid positive close prices are available.")

    fast_average = close.rolling(fast, min_periods=fast).mean()
    slow_average = close.rolling(slow, min_periods=slow).mean()
    signal = (fast_average > slow_average).fillna(False)
    position = signal.shift(1, fill_value=False).astype(bool)
    entries = int((position & ~position.shift(1, fill_value=False)).sum())
    buy_hold = pd.Series(True, index=close.index)
    results = {
        "fast_window": int(fast),
        "slow_window": int(slow),
        "signal_shift_bars": 1,
        "assumptions": (
            "Close-to-close returns; crossover signal is shifted one bar; "
            "no fees, slippage, or short positions."
        ),
        "sma_crossover": _measure_strategy(close, position, entries),
        "buy_and_hold": _measure_strategy(close, buy_hold, 1),
    }
    return results


def write_backtest(
    frame: pd.DataFrame,
    fast: int = 20,
    slow: int = 50,
    output_path: str | Path = "backtest.json",
) -> dict[str, Any]:
    results = run_backtest(frame, fast, slow)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="clean.csv", help="Clean CSV path.")
    parser.add_argument("--output", default="backtest.json", help="JSON output path.")
    parser.add_argument("--fast", type=int, default=20, help="Fast SMA window.")
    parser.add_argument("--slow", type=int, default=50, help="Slow SMA window.")
    args = parser.parse_args()
    try:
        frame = pd.read_csv(args.input)
        results = write_backtest(frame, args.fast, args.slow, args.output)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.error(str(error))
    print(f"Backtest complete; wrote {args.output}.")


if __name__ == "__main__":
    main()
