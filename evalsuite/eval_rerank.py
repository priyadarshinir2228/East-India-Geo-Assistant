"""Task 6: rerank the top N (10, 20, 50) of graph-hybrid with the cross-encoder on holdout queries.
Reports nDCG@5 and MRR before/after, extra time per query, batch-size effect and a determinism check."""
import argparse
import time

from common import config
from common.io import write_md_table
from evalsuite import qrels as Q
from evalsuite.metrics import mean, ndcg_at_k, reciprocal_rank
from retrieve import rerank, search


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-scorer", action="store_true", help="also try the LLM yes/no scorer at N=10")
    a = ap.parse_args()
    hold = [q for q in Q.load("retrieval_judgments.jsonl") if q["split"] == "holdout"]
    cands = {q["id"]: search.graph_hybrid(q["query"], k=50) for q in hold}
    ids = lambda lst: [d["chunk_id"] for d in lst]  # noqa: E731
    rows = []
    before5 = mean(ndcg_at_k(ids(cands[q["id"]]), q["qrels"], 5) for q in hold)
    before_mrr = mean(reciprocal_rank(ids(cands[q["id"]]), q["qrels"]) for q in hold)
    rows.append(["no rerank (graph hybrid)", "-", f"{before5:.3f}", f"{before_mrr:.3f}", "0"])
    for n in [10, 20, 50]:
        nd, mrr, secs = [], [], []
        for q in hold:
            r, s = rerank.rerank(q["query"], cands[q["id"]], top_n=n)
            secs.append(s)
            nd.append(ndcg_at_k(ids(r), q["qrels"], 5))
            mrr.append(reciprocal_rank(ids(r), q["qrels"]))
        rows.append(["cross-encoder", n, f"{mean(nd):.3f}", f"{mean(mrr):.3f}", f"{mean(secs) * 1000:.0f}"])
    if a.llm_scorer:
        nd, secs = [], []
        for q in hold:
            t = time.perf_counter()
            sc = [(rerank.llm_yes_score(q["query"], c["text"]), c["chunk_id"]) for c in cands[q["id"]][:10]]
            secs.append(time.perf_counter() - t)
            nd.append(ndcg_at_k([c for _, c in sorted(sc, key=lambda x: (-x[0], x[1]))], q["qrels"], 5))
        rows.append(["LLM P(yes), greedy", 10, f"{mean(nd):.3f}", "-", f"{mean(secs) * 1000:.0f}"])
    # batch size effect at N = 50
    brows = []
    for bs in [1, 8, 16, 32]:
        t = time.perf_counter()
        for q in hold:
            rerank.rerank(q["query"], cands[q["id"]], top_n=50, batch_size=bs)
        brows.append([bs, f"{(time.perf_counter() - t) / len(hold) * 1000:.0f}"])
    # determinism: two runs give the same order (ties broken by chunk_id)
    same = all(ids(rerank.rerank(q["query"], cands[q["id"]], 20)[0]) == ids(rerank.rerank(q["query"], cands[q["id"]], 20)[0]) for q in hold)
    write_md_table(config.RESULTS / "task6_rerank.md", "Task 6: reranking on holdout (10 queries)",
                   ["Scorer", "N", "nDCG@5", "MRR", "Extra ms/query"], rows,
                   notes="**Batch size (N = 50)**\n\n| Batch size | ms/query |\n|---|---|\n" +
                         "\n".join(f"| {b} | {t} |" for b, t in brows) +
                         f"\n\nDeterminism: two runs gave the same order for every query: {same}.")


if __name__ == "__main__":
    main()
