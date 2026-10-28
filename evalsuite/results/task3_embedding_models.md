## Task 3: embedding model comparison

| Model | Dims | Chunks/s (CPU) | Recall@5 (q01-q10) | Raw float32 size | Query / passage prefix |
|---|---|---|---|---|---|
| BAAI/bge-small-en-v1.5 | 384 | 10.0 | 0.633 | 0.24 MB | 'Represent this sentence for searching relevant passages: ' / '' |
| intfloat/e5-base-v2 | 768 | 3.1 | 0.850 | 0.47 MB | 'query: ' / 'passage: ' |

162 chunks. Pick the model with the better recall unless the speed cost is large; set EMBED_MODEL in .env and rerun es.setup_indices --recreate with its dims if it changes.
