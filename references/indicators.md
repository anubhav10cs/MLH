# Indicator and risk formulas

This reference is loaded only when formula details are needed. All calculations use the cleaned positive close-price series, in chronological order. Let `P_t` denote a close, `r_t = P_t / P_(t-1) - 1`, and use 252 trading days per year.

| Measure | Formula / convention |
| --- | --- |
| SMA(n) | Arithmetic mean of the latest `n` closes; unavailable before `n` observations. |
| EMA(n) | Exponential weighted mean with `alpha = 2 / (n + 1)`, `adjust=False`; unavailable before `n` observations. |
| RSI(14) | Wilder-style exponentially smoothed gains/losses (`alpha = 1/14`); `100 - 100/(1 + average_gain/average_loss)`. Flat series gives 50; gains with no losses gives 100. |
| MACD | EMA(12) minus EMA(26); signal is EMA(9) of the MACD line; histogram is line minus signal. |
| Daily return | Latest `r_t`. |
| Cumulative return | `P_last / P_first - 1`. |
| Annualized return | `(P_last / P_first) ** (252 / number_of_returns) - 1`. |
| Annualized volatility | Sample standard deviation of daily returns (`ddof=1`) times `sqrt(252)`. |
| Sharpe (rf=0) | Mean daily return divided by sample daily standard deviation, times `sqrt(252)`. |
| Maximum drawdown | Minimum of `P_t / running_max(P) - 1`. |
| Backtest CAGR | `(ending_equity / starting_equity) ** (252 / (observations - 1)) - 1`. |

Insufficient histories or zero return variance produce JSON `null` for unavailable values rather than NaN or infinity.
