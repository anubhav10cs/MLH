# Workflow details

## Column mapping

Column names are matched case-insensitively after removing spaces and punctuation. Recognized aliases include date/datetime/timestamp/time; open/open price; high/high price; low/low price; close/close price/adjusted close/adj close/LTP/last traded price/price/settle; and volume/vol/traded volume/quantity. The close column is required. OHLCV fields other than close are optional. Numeric fields are coerced; rows with invalid or non-positive closes are dropped. Invalid dates are dropped when a date column is present, and remaining rows are sorted chronologically. Inputs with fewer than 30 usable rows produce a warning.

CSV and Parquet (`.parquet` or `.pq`) are accepted. Parquet decoding uses pandas and therefore requires an installed pandas engine such as `pyarrow` or `fastparquet`; those engines are optional and intentionally not pinned in the core requirements.

## Minimum-data edge cases

- Rolling averages and MACD remain unavailable until their full windows exist.
- RSI, volatility, and Sharpe may be unavailable for short or constant series.
- Annualized return is unavailable with fewer than two usable prices.
- JSON outputs use `null` for mathematically undefined values.
- A date column is optional; date fields in the report are omitted when absent.
- Every input close must be finite and strictly positive for the return and drawdown formulas.

## Backtest assumptions

The crossover is long when SMA(fast) exceeds SMA(slow), otherwise flat. The close-derived signal is shifted by one bar before it is multiplied by close-to-close returns. Thus no position can earn the return that created its signal. The report counts each entry as one trade; trade win rate is calculated from each contiguous held interval, including an open final interval marked to market. Buy-and-hold is continuously long and is reported as one trade. Both use close prices and omit transaction costs, dividends, slippage, and short selling.

## Open-weight narration

Narration posts computed metrics to Ollama's `/api/generate` endpoint with `stream: false`. `OLLAMA_HOST` sets the base URL (default `http://localhost:11434`); `OLLAMA_MODEL` selects the default model (default `qwen2.5:7b`), and `--model` overrides it. Use a locally hosted or otherwise appropriately secured Ollama deployment. The prompt directs the model to use only the supplied numbers; calculation and fallback narration remain local and deterministic. Any request, decoding, or response error is reported on stderr and uses the deterministic template. `--no-llm` never attempts a network request.
