---
name: quant-analyst
description: Analyze historical OHLCV or price data in CSV or Parquet files when asked for technical indicators, risk statistics, a simple long-only moving-average backtest, or a plain-English market-data briefing. Use this skill for reproducible, data-grounded analysis; it is not for price predictions or personalized investment advice.
license: MIT
allowed-tools: Bash Read Write
---

# Quant Analyst

Analyze historical price data with deterministic Python calculations and an optional open-weight language model for narration. The model is never a source of financial figures.

## When to use

Use when an agent needs to inspect historical OHLCV/price data, compute common indicators and risk metrics, compare a simple moving-average strategy with buy-and-hold, or explain those results in plain English. Input may be CSV or Parquet. This skill does not forecast returns or provide personalized financial advice.

## Workflow

1. Load and clean the source data:
   `python scripts/load_data.py INPUT_FILE`
   This writes `clean.csv` in the current working directory.
2. Compute indicators and risk metrics:
   `python scripts/indicators.py`
   This reads `clean.csv` and writes `metrics.json`.
3. Run the long-only moving-average crossover backtest:
   `python scripts/backtest.py --fast 20 --slow 50`
   This reads `clean.csv` and writes `backtest.json`.
4. Write the briefing from computed outputs:
   `python scripts/summarize.py`
   This reads `metrics.json` and `backtest.json`; use `--no-llm` to select the deterministic template.
5. For a single command that runs all stages and prints the report:
   `python scripts/run.py INPUT_FILE --fast 20 --slow 50`
   Add `--model MODEL_NAME` to select an Ollama model or `--no-llm` to disable model access.

## Rules

- Calculate every figure in Python. Never ask a language model to calculate or supply a number.
- Use only the supplied computed metrics when narrating; do not invent values, causes, forecasts, or missing data.
- Shift the crossover signal by one bar before applying returns to prevent look-ahead bias.
- State data limitations and keep the briefing descriptive, not prescriptive.
- If Ollama is unavailable or returns an error, report the fallback and use the deterministic template.
- End every briefing with: `Not financial advice.`

## Files

- `scripts/load_data.py` — read, map, clean, and sort CSV/Parquet input.
- `scripts/indicators.py` — calculate indicators and risk metrics.
- `scripts/backtest.py` — compare SMA crossover with buy-and-hold.
- `scripts/summarize.py` — narrate metrics with Ollama or a deterministic fallback.
- `scripts/run.py` — run the complete pipeline from the command line.
- `references/indicators.md` — indicator and risk formulas, loaded as needed.
- `references/workflow.md` — mappings, edge cases, backtest assumptions, and model notes.
- `examples/sample_nifty.csv` — reproducible synthetic daily price data for a demo.
