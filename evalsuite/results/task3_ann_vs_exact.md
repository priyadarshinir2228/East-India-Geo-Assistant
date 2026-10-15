## Task 3: approximate vs exact kNN

| Method | num_candidates | Recall@10 vs exact | Latency ms/query |
|---|---|---|---|
| exact (NumPy brute force) | - | 1.000 | 1.01 |
| int8_hnsw | 10 | 0.930 | 57.59 |
| int8_hnsw | 20 | 0.970 | 70.96 |
| int8_hnsw | 50 | 0.980 | 45.19 |
| int8_hnsw | 100 | 0.980 | 41.95 |
| hnsw float32 | 10 | 0.950 | 46.78 |
| hnsw float32 | 20 | 1.000 | 35.43 |
| hnsw float32 | 50 | 1.000 | 26.20 |
| hnsw float32 | 100 | 1.000 | 24.06 |

162 vectors, 384 dims, 20 queries (q01-q20). Latency is the client-side round trip.

On disk: `embedding` (int8_hnsw) 306 KiB, `embedding_f32` (hnsw) 245 KiB, whole index 1221 KiB. Note: int8_hnsw keeps the raw float vectors too (for rescoring), so its saving shows in the memory needed for search, about 4x smaller.
