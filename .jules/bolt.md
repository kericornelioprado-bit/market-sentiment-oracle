## 2025-05-23 - Batch Processing FinBERT
**Learning:** Replacing `df.apply` with batch processing (size 32) yielded ~3.7x speedup. Critical lesson: Assigning lists/arrays back to a filtered DataFrame column (`df['col'] = list`) respects index alignment in Pandas. If the DataFrame was filtered, the indices are discontinuous, and direct assignment will fail or produce NaNs.
**Action:** Always use `.values` (e.g., `df['col'] = np.array(list).values`) or ensure index alignment when assigning batch results back to a subset of a DataFrame. Also, explicit `.to(model.device)` is needed for batch inputs.

## 2025-05-24 - Vectorized Tensor Post-processing
**Learning:** Iterating over PyTorch tensors in Python to find max values/indices (`max(scores)`, `scores.index()`) is significantly slower than using `torch.max(dim=1)`. Vectorizing this step yielded a ~2.8x speedup for the post-processing phase of FinBERT inference.
**Action:** When working with batch predictions from models, always perform reduction operations (max, min, mean) on the tensor directly before moving data to CPU/Python lists.
