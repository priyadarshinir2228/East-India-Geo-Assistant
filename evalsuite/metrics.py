"""Metric functions written from their definitions (no library calls).

Retrieval metrics take `ranked` (list of ids, best first) and `qrels` (dict id -> grade 0/1/2).
A result counts as relevant when its grade >= 1.
"""
import math


# ---------- extraction ----------
def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def match_mentions(pred, gold, relaxed=False):
    """Greedy one-to-one matching of (type, start, end) spans. Returns tp, fp, fn.

    exact: same type and identical span. relaxed: same type and spans overlap.
    Each gold span can be matched at most once.
    """
    used, tp = set(), 0
    for p in sorted(pred, key=lambda m: (m["start"], m["end"])):
        for gi, g in enumerate(gold):
            if gi in used or g["type"] != p["type"]:
                continue
            hit = (p["start"] == g["start"] and p["end"] == g["end"]) if not relaxed else \
                (p["start"] < g["end"] and g["start"] < p["end"])
            if hit:
                used.add(gi)
                tp += 1
                break
    return tp, len(pred) - tp, len(gold) - tp


# ---------- retrieval ----------
def precision_at_k(ranked, qrels, k):
    return sum(1 for d in ranked[:k] if qrels.get(d, 0) >= 1) / k


def recall_at_k(ranked, qrels, k):
    n_rel = sum(1 for g in qrels.values() if g >= 1)
    if n_rel == 0:
        return 0.0
    return sum(1 for d in ranked[:k] if qrels.get(d, 0) >= 1) / n_rel


def reciprocal_rank(ranked, qrels, k=None):
    for i, d in enumerate(ranked[:k] if k else ranked, start=1):
        if qrels.get(d, 0) >= 1:
            return 1.0 / i
    return 0.0


def dcg(gains):
    # gain (2^g - 1) rewards grade-2 results more than grade-1; log2(i + 1) discounts lower ranks
    return sum((2 ** g - 1) / math.log2(i + 1) for i, g in enumerate(gains, start=1))


def ndcg_at_k(ranked, qrels, k):
    actual = dcg([qrels.get(d, 0) for d in ranked[:k]])
    ideal = dcg(sorted(qrels.values(), reverse=True)[:k])
    return actual / ideal if ideal > 0 else 0.0


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


# ---------- calibration ----------
def brier(probs, labels):
    return mean((p - y) ** 2 for p, y in zip(probs, labels))


def log_loss(probs, labels, eps=1e-12):
    return mean(-(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps))) for p, y in zip(probs, labels))


def reliability_table(probs, labels, n_bins=5):
    """Equal-width bins on [0, 1]. Returns rows (lo, hi, count, mean_conf, accuracy)."""
    rows = []
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        idx = [i for i, p in enumerate(probs) if (lo <= p < hi) or (b == n_bins - 1 and p == 1.0)]
        if idx:
            rows.append((lo, hi, len(idx), mean(probs[i] for i in idx), mean(labels[i] for i in idx)))
        else:
            rows.append((lo, hi, 0, None, None))
    return rows


def ece(probs, labels, n_bins=5):
    """Expected calibration error: sum over bins of (bin share) * |accuracy - mean confidence|."""
    n = len(probs)
    return sum(c / n * abs(acc - conf) for _, _, c, conf, acc in reliability_table(probs, labels, n_bins) if c)


# ---------- vectors ----------
def cosine_matrix(q, m):
    """Cosine similarity of query vector q against each row of matrix m (NumPy arrays)."""
    import numpy as np
    qn = q / np.linalg.norm(q)
    mn = m / np.linalg.norm(m, axis=1, keepdims=True)
    return mn @ qn


def exact_top_k(q, m, ids, k):
    """Brute-force nearest neighbours: score every vector, then sort. Ties broken by id."""
    sims = cosine_matrix(q, m)
    order = sorted(range(len(ids)), key=lambda i: (-sims[i], ids[i]))[:k]
    return [ids[i] for i in order], [float(sims[i]) for i in order]
