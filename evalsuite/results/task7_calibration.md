## Task 7: reliability on test (15 questions, 5 bins)

| Bin | Count | Mean confidence | Success rate |
|---|---|---|---|
| 0.0-0.2 | 3 | 0.15 | 0.00 |
| 0.2-0.4 | 2 | 0.35 | 0.00 |
| 0.4-0.6 | 1 | 0.46 | 0.00 |
| 0.6-0.8 | 6 | 0.75 | 0.67 |
| 0.8-1.0 | 3 | 0.82 | 1.00 |

ECE = 0.177, Brier = 0.115 (combined, test). Mean confidence 0.57 vs success rate 0.47: the system is over-confident on average.

Logistic regression weights {'p_top': 1.979, 'margin': 0.403, 'agree': 1.013, 'lp_mean': 0.107}, intercept -1.898.

**Temperature scaling of the reranker probability (p_top alone)**

| T | log loss on fit |
|---|---|
| 0.5 | 0.272 |
| 0.75 | 0.219 |
| 1.0 | 0.204 |
| 1.5 | 0.213 |
| 2.0 | 0.241 |
| 2.5 | 0.273 |
| 3.0 | 0.304 |

Chosen T = 1.0. Test ECE of sigmoid(s): T=1 -> 0.133; T=1.0 -> 0.133.
