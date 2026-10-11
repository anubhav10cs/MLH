# quant-analyst

An open-source Agent Skill for reproducible analysis of historical OHLCV or price data. It cleans CSV/Parquet input, computes technical indicators and risk statistics in Python, runs a simple long-only moving-average backtest, and produces a plain-English briefing.

Built for MLH Hacktoberfest 2026's **Open Source AI** theme, the project pairs transparent, reproducible numerical analysis with optional locally hosted open-weight narration.

## Why open-weight AI is core

The optional narration stage calls an open-weight model served by [Ollama](https://ollama.com/), by default `qwen2.5:7b`. The model receives already-computed JSON and is instructed to explain only those figures. It does not calculate indicators, backtest results, or risk values. This keeps the numerical analysis deterministic while making the explanation auditable and runnable with locally hosted weights. If Ollama is unavailable, a deterministic Python template produces the briefing instead. No proprietary inference API is used.

## Quickstart

Requires Python 3, pandas, and NumPy:

```bash
python -m pip install -r requirements.txt
python scripts/run.py examples/sample_nifty.csv --no-llm
```

The example uses a fixed random seed and works without external data or model access. To narrate with Ollama, start Ollama, pull a model such as `qwen2.5:7b`, then run:

```bash
ollama pull qwen2.5:7b
python scripts/run.py examples/sample_nifty.csv --model qwen2.5:7b
```

For Parquet input, pandas also needs a compatible optional engine such as `pyarrow`; install it separately if your environment does not already provide one.

## Use as an agent skill

Place this directory in an agent's skills location, or expose its `SKILL.md` in a compatible Agent Skill environment. The frontmatter follows the Agent Skill Open Standard's core format and uses only `scripts/` and `references/` alongside the skill entry point. An agent can load the workflow and call the scripts with its permitted shell, read, and write tools.

## Pipeline

| Stage | Script | Output |
| --- | --- | --- |
| Load CSV/Parquet, map aliases, coerce values, sort by date | `scripts/load_data.py` | `clean.csv` |
| Compute SMA, EMA, RSI, MACD, returns, volatility, Sharpe, drawdown | `scripts/indicators.py` | `metrics.json` |
| Compare shifted long-only SMA crossover and buy-and-hold | `scripts/backtest.py` | `backtest.json` |
| Explain computed results with Ollama or a deterministic fallback | `scripts/summarize.py` | Briefing on stdout |
| Run all stages and print a clean report | `scripts/run.py` | All outputs and report |

## Remote inference

For a remote Ollama host (for example, a DigitalOcean-hosted Ollama instance), set `OLLAMA_HOST` to its base URL, including the scheme and port, then run the normal command:

```bash
# PowerShell
$env:OLLAMA_HOST = "http://your-ollama-host:11434"
python scripts/run.py examples/sample_nifty.csv
```

Use a securely reachable host and configure network access appropriately. `OLLAMA_MODEL` selects the default model when `--model` is omitted. The default host is `http://localhost:11434`.

## Example output

Output varies with the current pipeline result; in `--no-llm` mode the wording is deterministic. A run prints a report with:

```text
QUANT ANALYST BRIEFING
Data: 520 rows from 2024-01-01T00:00:00Z to 2025-12-26T00:00:00Z
Strategy: SMA 20/50

The analysis covers 520 valid observations from 2024-01-01T00:00:00Z to
2025-12-26T00:00:00Z, with the latest close at 29,814.73. The 20-day SMA is
29,446.75, the 50-day SMA is 28,532.95, and RSI(14) is 62.03. Over the
available period, cumulative return was 36.14%; annualized return was 16.16%
and annualized volatility was 14.64%. Maximum drawdown was -25.85%, and the
zero-risk-free-rate Sharpe ratio was 1.10. The shifted 20/50 SMA crossover
returned 34.31% with 5 trades and a trade win rate of 40.00%; buy-and-hold
returned 36.14%. The backtest excludes fees and slippage, and historical
results do not establish future performance. Interpret these descriptive
statistics in light of the input's coverage and quality.
Not financial advice.
```

All displayed figures are derived from the input in Python. The sample price path is synthetic and is not a representation of actual NIFTY history.

## License

MIT. See [LICENSE](LICENSE).
