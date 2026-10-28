## Task 7: coverage and accuracy by threshold

| Threshold | Coverage (fit) | Accuracy (fit) | Coverage (test) | Accuracy (test) |  |
|---|---|---|---|---|---|
| 0.3 | 0.84 | 0.67 | 0.80 | 0.58 |  |
| 0.4 | 0.64 | 0.88 | 0.67 | 0.70 |  |
| 0.5 | 0.56 | 0.93 | 0.60 | 0.78 | chosen |
| 0.6 | 0.52 | 0.92 | 0.60 | 0.78 |  |
| 0.7 | 0.48 | 1.00 | 0.53 | 0.88 |  |
| 0.8 | 0.20 | 1.00 | 0.20 | 1.00 |  |

Threshold 0.5 is the lowest with >= 90% accuracy on the fit questions. It is saved to confidence_model.json and used by the assistant.
