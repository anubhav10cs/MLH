"""Run the complete quant-analyst data pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from backtest import write_backtest
from indicators import write_metrics
from load_data import load_data
from summarize import narrate


def run(
    input_path: str | Path,
    fast: int = 20,
    slow: int = 50,
    model: str | None = None,
    no_llm: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    frame = load_data(input_path, "clean.csv")
    metrics = write_metrics(frame, "metrics.json")
    backtest = write_backtest(frame, fast, slow, "backtest.json")
    briefing = narrate(metrics, backtest, model=model, no_llm=no_llm)
    return metrics, backtest, briefing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Input CSV or Parquet file.")
    parser.add_argument("--fast", type=int, default=20, help="Fast SMA window.")
    parser.add_argument("--slow", type=int, default=50, help="Slow SMA window.")
    parser.add_argument("--model", help="Ollama model name.")
    parser.add_argument("--no-llm", action="store_true", help="Use local template.")
    args = parser.parse_args()
    try:
        metrics, backtest, briefing = run(
            args.path, args.fast, args.slow, args.model, args.no_llm
        )
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))

    print("QUANT ANALYST BRIEFING")
    print(
        f"Data: {metrics['rows']} rows"
        + (
            f" from {metrics['start_date']} to {metrics['end_date']}"
            if metrics.get("start_date") and metrics.get("end_date")
            else ""
        )
    )
    print(f"Strategy: SMA {backtest['fast_window']}/{backtest['slow_window']}")
    print()
    print(briefing)
    print()
    print("Wrote clean.csv, metrics.json, and backtest.json.")


if __name__ == "__main__":
    main()
