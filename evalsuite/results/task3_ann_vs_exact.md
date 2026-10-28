## Task 3: approximate vs exact kNN

| Method | num_candidates | Recall@10 vs exact | Latency ms/query |
|---|---|---|---|
| exact (NumPy brute force) | - | 1.000 | 0.29 |
| int8_hnsw | 10 | 0.930 | 20.28 |
| int8_hnsw | 20 | 0.970 | 20.19 |
| int8_hnsw | 50 | 0.980 | 23.24 |
| int8_hnsw | 100 | 0.980 | 19.93 |
| hnsw float32 | 10 | 0.950 | 19.79 |
| hnsw float32 | 20 | 1.000 | 23.34 |
| hnsw float32 | 50 | 1.000 | 18.72 |
| hnsw float32 | 100 | 1.000 | 18.79 |

162 vectors, 384 dims, 20 queries (q01-q20). Latency is the client-side round trip.

On disk: `embedding` (int8_hnsw) 306 KiB, `embedding_f32` (hnsw) 245 KiB, whole index 1221 KiB. Note: int8_hnsw keeps the raw float vectors too (for rescoring), so its saving shows in the memory needed for search, about 4x smaller.
