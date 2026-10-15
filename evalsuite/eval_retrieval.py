"""Task 5: every mode at k = 1, 3, 5, 10, 20; tune the RRF constant on tune queries and report holdout;
failure analysis by query type; optional MMR trade-off."""

from common import config
from common.io import write_md_table
from common.models import get_embedder
from evalsuite import qrels as Q
from evalsuite.metrics import mean, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank
from retrieve import search

KS = [1, 3, 5, 10, 20]


def run(mode, q, k=20, **kw):
    return [d["chunk_id"] for d in search.MODES[mode](q, k=k, **kw)]


def metrics_row(ranked_lists, queries, k):
    return (mean(precision_at_k(r, q["qrels"], k) for r, q in zip(ranked_lists, queries)),
            mean(recall_at_k(r, q["qrels"], k) for r, q in zip(ranked_lists, queries)),
            mean(reciprocal_rank(r, q["qrels"], k) for r, q in zip(ranked_lists, queries)),
            mean(ndcg_at_k(r, q["qrels"], k) for r, q in zip(ranked_lists, queries)))


def mmr(query, cands, lam=0.7, k=5):
    """Maximal marginal relevance: pick greedily max(lam * sim(q, d) - (1 - lam) * max sim(d, chosen))."""
    emb = get_embedder()
    qv = emb.query(query)
    dv = emb.passages([c["text"] for c in cands])
    rel = dv @ qv
    chosen = []
    while len(chosen) < min(k, len(cands)):
        best, best_s = None, -1e9
        for i in range(len(cands)):
            if i in chosen:
                continue
            red = max((float(dv[i] @ dv[j]) for j in chosen), default=0.0)
            s = lam * float(rel[i]) - (1 - lam) * red
            if s > best_s:
                best, best_s = i, s
        chosen.append(best)
    return [cands[i]["chunk_id"] for i in chosen]


def main():
    qs = Q.load("retrieval_judgments.jsonl")
    tune, hold = [q for q in qs if q["split"] == "tune"], [q for q in qs if q["split"] == "holdout"]
    runs = {m: [run(m, q["query"]) for q in qs] for m in search.MODES}
    rows = []
    for m in search.MODES:
        for k in KS:
            p, r, mrr, nd = metrics_row(runs[m], qs, k)
            rows.append([m, k, f"{p:.3f}", f"{r:.3f}", f"{mrr:.3f}", f"{nd:.3f}"])
    write_md_table(config.RESULTS / "task5_modes_by_k.md", "Task 5: all modes, all 30 queries",
                   ["Mode", "k", "P@k", "R@k", "MRR@k", "nDCG@k"], rows,
                   notes="Default k = 5 unless the table shows recall still climbing steeply between 5 and 10.")

    # tuning: RRF constant on tune queries only (graph mode), then report holdout
    grid, trows = [1, 10, 30, 60, 100], []
    for kc in grid:
        nd = mean(ndcg_at_k(run("graph", q["query"], k_const=kc), q["qrels"], 5) for q in tune)
        trows.append([kc, f"{nd:.3f}"])
    best = max(grid, key=lambda kc: float(trows[grid.index(kc)][1]))
    base = mean(ndcg_at_k(run("graph", q["query"], k_const=60), q["qrels"], 5) for q in hold)
    tuned = mean(ndcg_at_k(run("graph", q["query"], k_const=best), q["qrels"], 5) for q in hold)
    write_md_table(config.RESULTS / "task5_tuning.md", "Task 5: tuning the RRF constant (graph mode, nDCG@5)",
                   ["RRF k", "nDCG@5 on tune (20)"], trows,
                   notes=f"Best on tune: k = {best}. Holdout (10 queries): default k=60 -> {base:.3f}, tuned k={best} -> {tuned:.3f}. "
                         f"Gain held: {'yes' if tuned >= base else 'no'}.")

    # failure analysis by query type (nDCG@5)
    types = sorted({q["type"] for q in qs})
    frows = []
    for t in types:
        idx = [i for i, q in enumerate(qs) if q["type"] == t]
        scores = {m: mean(ndcg_at_k(runs[m][i], qs[i]["qrels"], 5) for i in idx) for m in search.MODES}
        win = max(scores, key=scores.get)
        frows.append([t, len(idx)] + [f"{scores[m]:.3f}" for m in search.MODES] + [win])
    write_md_table(config.RESULTS / "task5_by_type.md", "Task 5: nDCG@5 by query type",
                   ["Type", "n"] + list(search.MODES) + ["Winner"], frows)

    # optional MMR on hybrid candidates
    mrows = []
    for lam in [1.0, 0.7, 0.5, 0.3]:
        lists = [mmr(q["query"], search.hybrid(q["query"], 20), lam, 5) for q in qs]
        docs = mean(len({c.split(":")[0] for c in lst}) for lst in lists)
        nd = mean(ndcg_at_k(lst, q["qrels"], 5) for lst, q in zip(lists, qs))
        mrows.append([lam, f"{nd:.3f}", f"{docs:.2f}"])
    write_md_table(config.RESULTS / "task5_mmr.md", "Task 5 (optional): MMR trade-off on hybrid top-20",
                   ["lambda (1 = relevance only)", "nDCG@5", "distinct documents in top 5"], mrows)


if __name__ == "__main__":
    main()
