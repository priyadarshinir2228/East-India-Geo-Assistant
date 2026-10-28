## Task 6: reranking on holdout (10 queries)

| Scorer | N | nDCG@5 | MRR | Extra ms/query |
|---|---|---|---|---|
| no rerank (graph hybrid) | - | 0.885 | 1.000 | 0 |
| cross-encoder | 10 | 0.863 | 1.000 | 4620 |
| cross-encoder | 20 | 0.843 | 1.000 | 8500 |
| cross-encoder | 50 | 0.843 | 1.000 | 24463 |
| LLM P(yes), greedy | 10 | 0.912 | - | 70255 |

**Batch size (N = 50)**

| Batch size | ms/query |
|---|---|
| 1 | 27311 |
| 8 | 27695 |
| 16 | 27052 |
| 32 | 33875 |

Determinism: two runs gave the same order for every query: True.
