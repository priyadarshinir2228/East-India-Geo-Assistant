## Task 5: tuning the RRF constant (graph mode, nDCG@5)

| RRF k | nDCG@5 on tune (20) |
|---|---|
| 1 | 0.758 |
| 10 | 0.787 |
| 30 | 0.774 |
| 60 | 0.765 |
| 100 | 0.759 |

Best on tune: k = 10. Holdout (10 queries): default k=60 -> 0.885, tuned k=10 -> 0.887. Gain held: yes.
