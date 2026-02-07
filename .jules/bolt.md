## 2025-05-23 - Batch Processing FinBERT
**Learning:** Replacing `df.apply` with batch processing (size 32) yielded ~3.7x speedup. Critical lesson: Assigning lists/arrays back to a filtered DataFrame column (`df['col'] = list`) respects index alignment in Pandas. If the DataFrame was filtered, the indices are discontinuous, and direct assignment will fail or produce NaNs.
**Action:** Always use `.values` (e.g., `df['col'] = np.array(list).values`) or ensure index alignment when assigning batch results back to a subset of a DataFrame. Also, explicit `.to(model.device)` is needed for batch inputs.

## 2025-05-24 - Vectorized Tensor Post-processing
**Learning:** Iterating over PyTorch tensors in Python to find max values/indices (`max(scores)`, `scores.index()`) is significantly slower than using `torch.max(dim=1)`. Vectorizing this step yielded a ~2.8x speedup for the post-processing phase of FinBERT inference.
**Action:** When working with batch predictions from models, always perform reduction operations (max, min, mean) on the tensor directly before moving data to CPU/Python lists.

## 2025-05-25 - Log Returns Optimization
**Learning:** `np.log(series).diff()` is ~25% faster than `np.log(series / series.shift(1))` for calculating log returns. Division is significantly more expensive than subtraction, and `np.log` cost is similar (or slightly cheaper as `diff` is optimized).
**Action:** Prefer `log(x).diff()` over `log(x/x_prev)` for time series differencing when values are positive.

## 2025-05-26 - RSI Formula Optimization
**Learning:** Calculating RSI as `100 * Gain / (Gain + Loss)` is ~1.5x faster than the standard `100 - (100 / (1 + RS))` formula. It avoids one division and one subtraction operation, and naturally handles the `Loss=0` case (avoiding `inf` without extra checks).
**Action:** Prefer the algebraic simplification `Gain / (Gain + Loss)` for normalized ratios when applicable to reduce operation count and improve numerical stability.

## 2025-05-27 - yfinance Batch Download Optimization
**Learning:** `yfinance.download(tickers)` in batch is >3x faster than sequential downloads. However, it returns a MultiIndex DataFrame (Levels: Ticker, Price) when `group_by='ticker'` is used, even for a single ticker in the list. Sequential download logic (SingleIndex) must be adapted to extract `data[ticker]`.
**Action:** Always prefer batch downloads for multiple tickers. Use `group_by='ticker'` and iterate through the top level to extract individual DataFrames. Explicitly handle `dropna(how='all')` to remove empty rows caused by the union of dates across all tickers.
