"""Narrate computed metrics with Ollama or a deterministic template."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = (
    "You are a cautious quantitative analyst. Explain the supplied computed "
    "metrics in plain English in 120-180 words. Use only the numbers and facts "
    "provided in the JSON; do not calculate, infer, or invent any figures, "
    "causes, forecasts, or data not present there. Describe limitations without "
    "making recommendations. End with the exact sentence: Not financial advice."
)


def _format_percent(value: Any) -> str:
    return "unavailable" if value is None else f"{float(value) * 100:.2f}%"


def _format_number(value: Any) -> str:
    return "unavailable" if value is None else f"{float(value):,.2f}"


def deterministic_summary(
    metrics: dict[str, Any], backtest: dict[str, Any]
) -> str:
    indicators = metrics["indicators"]
    risk = metrics["risk"]
    crossover = backtest["sma_crossover"]
    buy_hold = backtest["buy_and_hold"]
    dates = (
        f" from {metrics['start_date']} to {metrics['end_date']}"
        if metrics.get("start_date") and metrics.get("end_date")
        else ""
    )
    lines = [
        (
            f"The analysis covers {metrics['rows']} valid observations{dates}, "
            f"with the latest close at {_format_number(metrics['latest_close'])}."
        ),
        (
            f"The 20-day SMA is {_format_number(indicators['sma_20'])}, the "
            f"50-day SMA is {_format_number(indicators['sma_50'])}, and RSI(14) "
            f"is {_format_number(indicators['rsi_14'])}."
        ),
        (
            f"Over the available period, cumulative return was "
            f"{_format_percent(risk['cumulative_return'])}; annualized return "
            f"was {_format_percent(risk['annualized_return'])} and annualized "
            f"volatility was {_format_percent(risk['annualized_volatility'])}."
        ),
        (
            f"Maximum drawdown was {_format_percent(risk['max_drawdown'])}, "
            f"and the zero-risk-free-rate Sharpe ratio was "
            f"{_format_number(risk['sharpe_ratio_rf_0'])}."
        ),
        (
            f"The shifted {backtest['fast_window']}/{backtest['slow_window']} "
            f"SMA crossover returned {_format_percent(crossover['total_return'])} "
            f"with {crossover['num_trades']} trades and a trade win rate of "
            f"{_format_percent(crossover['trade_win_rate'])}; buy-and-hold "
            f"returned {_format_percent(buy_hold['total_return'])}."
        ),
        (
            "The backtest excludes fees and slippage, and historical results "
            "do not establish future performance. Interpret these descriptive "
            "statistics in light of the input's coverage and quality."
        ),
        "Not financial advice.",
    ]
    return " ".join(lines)


def narrate(
    metrics: dict[str, Any],
    backtest: dict[str, Any],
    model: str | None = None,
    no_llm: bool = False,
) -> str:
    if no_llm:
        return deterministic_summary(metrics, backtest)

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    selected_model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    payload = {
        "model": selected_model,
        "system": SYSTEM_PROMPT,
        "prompt": json.dumps(
            {"metrics": metrics, "backtest": backtest},
            ensure_ascii=False,
            allow_nan=False,
        ),
        "stream": False,
    }
    try:
        request = urllib.request.Request(
            f"{host}/api/generate",
            data=json.dumps(payload, allow_nan=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not isinstance(body, dict):
            raise ValueError("Ollama returned a non-object response.")
        text = body.get("response")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Ollama returned an empty or invalid response.")
        return text.strip()
    except (
        OSError,
        urllib.error.URLError,
        http.client.HTTPException,
        json.JSONDecodeError,
        UnicodeDecodeError,
        ValueError,
        TypeError,
    ) as error:
        print(
            f"Warning: Ollama narration failed ({error}); using deterministic "
            "summary.",
            file=sys.stderr,
        )
        return deterministic_summary(metrics, backtest)


def _read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as source:
        result = json.load(source)
    if not isinstance(result, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", default="metrics.json", help="Metrics JSON.")
    parser.add_argument("--backtest", default="backtest.json", help="Backtest JSON.")
    parser.add_argument("--model", help="Ollama model name.")
    parser.add_argument("--no-llm", action="store_true", help="Use local template.")
    args = parser.parse_args()
    try:
        metrics = _read_json(args.metrics)
        backtest = _read_json(args.backtest)
        briefing = narrate(metrics, backtest, args.model, args.no_llm)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(briefing)


if __name__ == "__main__":
    main()
