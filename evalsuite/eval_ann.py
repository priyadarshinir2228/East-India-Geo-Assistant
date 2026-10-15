"""Task 3.5 / 3.6: exact (own NumPy) top-10 vs approximate kNN at several num_candidates,
for the int8-quantised field and the float field; plus index size on disk per field."""
import time

import numpy as np
from elasticsearch import helpers

from common import config
from common.es import admin_client, app_client
from common.io import read_jsonl, write_md_table
from common.models import get_embedder
from evalsuite.metrics import exact_top_k, mean
from retrieve import search


def main():
    es = app_client()
    ids, vecs = [], []
    for h in helpers.scan(es, index=config.CHUNKS_INDEX, query={"query": {"match_all": {}}}, _source=["chunk_id", "embedding_f32"]):
        ids.append(h["_source"]["chunk_id"])
        vecs.append(h["_source"]["embedding_f32"])
    mat = np.array(vecs, dtype=np.float32)
    qs = [q["query"] for q in read_jsonl(config.EVAL_DIR / "retrieval_judgments.jsonl")[:20]]
    emb = get_embedder()
    qv = [emb.query(q) for q in qs]
    t = time.perf_counter()
    exact = [exact_top_k(v, mat, ids, 10)[0] for v in qv]
    exact_ms = (time.perf_counter() - t) / len(qs) * 1000
    rows = [["exact (NumPy brute force)", "-", "1.000", f"{exact_ms:.2f}"]]
    for field, label in [("embedding", "int8_hnsw"), ("embedding_f32", "hnsw float32")]:
        for nc in [10, 20, 50, 100]:
            recs, lat = [], []
            for q, v, ex in zip(qs, qv, exact):
                search.vector(q, 10, num_candidates=nc, field=field, qvec=v)  # warm cache
                t = time.perf_counter()
                got = [d["chunk_id"] for d in search.vector(q, 10, num_candidates=nc, field=field, qvec=v)]
                lat.append((time.perf_counter() - t) * 1000)
                recs.append(len(set(got) & set(ex)) / 10)
            rows.append([label, nc, f"{mean(recs):.3f}", f"{mean(lat):.2f}"])
    notes = [f"{len(ids)} vectors, {mat.shape[1]} dims, 20 queries (q01-q20). Latency is the client-side round trip."]
    try:  # disk usage per field needs an admin privilege; this is a measurement, not the app
        du = admin_client().indices.disk_usage(index=config.CHUNKS_INDEX, run_expensive_tasks=True)
        fields = du[config.CHUNKS_INDEX]["fields"]
        size = lambda f: fields.get(f, {}).get("total_in_bytes", 0)  # noqa: E731
        notes.append(f"\nOn disk: `embedding` (int8_hnsw) {size('embedding') / 1024:.0f} KiB, "
                     f"`embedding_f32` (hnsw) {size('embedding_f32') / 1024:.0f} KiB, whole index "
                     f"{du[config.CHUNKS_INDEX]['store_size_in_bytes'] / 1024:.0f} KiB. Note: int8_hnsw keeps the raw float "
                     "vectors too (for rescoring), so its saving shows in the memory needed for search, about 4x smaller.")
    except Exception as e:  # noqa: BLE001
        notes.append(f"disk usage not available: {e}")
    write_md_table(config.RESULTS / "task3_ann_vs_exact.md", "Task 3: approximate vs exact kNN",
                   ["Method", "num_candidates", "Recall@10 vs exact", "Latency ms/query"], rows, notes="\n".join(notes))


if __name__ == "__main__":
    main()
