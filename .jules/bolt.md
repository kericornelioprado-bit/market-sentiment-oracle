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

## 2026-02-05 - yfinance Batch Download
**Learning:** `yf.download(TICKERS)` is >10x faster than sequential calls due to internal threading. However, it returns a MultiIndex DataFrame where dates are the union of all tickers' history. This injects `NaN` rows for tickers that weren't trading on certain dates (e.g. IPOs).
**Action:** Always verify data density after batch downloads. Use `df_batch[ticker].dropna(how='all')` to restore the dense format expected by downstream consumers.

## 2026-02-10 - Parallel API Ingestion
**Learning:** Sequential `requests.get` calls are an I/O bottleneck. Refactoring `fetch_news` to use `ThreadPoolExecutor` yielded a ~4x speedup (2.0s -> 0.5s for 4 items).
**Action:** When iterating over external API calls, always consider `concurrent.futures`. Ensure error handling is robust within threads to prevent partial failures from crashing the batch.
