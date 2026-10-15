"""Task 3.2: compare the two embedding models on dims, speed and recall@5 (first 10 queries).
Search is exact (NumPy brute force over all chunks) so the comparison is about the models, not the index."""
import time

import numpy as np

from common import config
from common.io import read_jsonl, write_md_table
from common.models import Embedder
from evalsuite import qrels as Q
from evalsuite.metrics import exact_top_k, mean, recall_at_k


def main():
    chunks = read_jsonl(config.WORK / "chunks.jsonl")
    texts = [c["title"] + "\n" + c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    queries = Q.load("retrieval_judgments.jsonl")[:10]
    rows = []
    for name in [config.EMBED_MODEL, config.EMBED_MODEL_B]:
        m = Embedder(name)
        m.passages(texts[:8])  # warm-up
        t = time.perf_counter()
        mat = m.passages(texts)
        cps = len(texts) / (time.perf_counter() - t)
        rec = mean(recall_at_k(exact_top_k(m.query(q["query"]), mat, ids, 5)[0], q["qrels"], 5) for q in queries)
        mb = mat.shape[1] * 4 * len(texts) / 2 ** 20
        rows.append([name, mat.shape[1], f"{cps:.1f}", f"{rec:.3f}", f"{mb:.2f} MB",
                     repr(m.q_prefix) + " / " + repr(m.p_prefix)])
        np.save(config.WORK / f"vectors_{name.split('/')[-1]}.npy", mat)
    write_md_table(config.RESULTS / "task3_embedding_models.md", "Task 3: embedding model comparison",
                   ["Model", "Dims", "Chunks/s (CPU)", "Recall@5 (q01-q10)", "Raw float32 size", "Query / passage prefix"], rows,
                   notes=f"{len(texts)} chunks. Pick the model with the better recall unless the speed cost is large; "
                         "set EMBED_MODEL in .env and rerun es.setup_indices --recreate with its dims if it changes.")


if __name__ == "__main__":
    main()
