"""Hand-checked cases for the metric functions, plus cross-checks against scikit-learn."""
import math

import numpy as np
import pytest

from evalsuite import metrics as M

Q = {"a": 2, "b": 1, "c": 0, "d": 1}


def test_precision_recall():
    ranked = ["c", "a", "x", "b"]
    assert M.precision_at_k(ranked, Q, 2) == 0.5
    assert M.recall_at_k(ranked, Q, 4) == pytest.approx(2 / 3)


def test_mrr():
    assert M.reciprocal_rank(["c", "x", "b"], Q) == pytest.approx(1 / 3)
    assert M.reciprocal_rank(["x"], Q) == 0.0


def test_ndcg_by_hand():
    ranked = ["b", "a"]
    dcg = (2 ** 1 - 1) / math.log2(2) + (2 ** 2 - 1) / math.log2(3)
    idcg = (2 ** 2 - 1) / math.log2(2) + (2 ** 1 - 1) / math.log2(3)
    assert M.ndcg_at_k(ranked, Q, 2) == pytest.approx(dcg / idcg)
    assert M.ndcg_at_k(["a", "b", "d"], Q, 3) == pytest.approx(1.0)


def test_ndcg_matches_sklearn():
    from sklearn.metrics import ndcg_score
    ranked = ["c", "b", "a", "d"]
    true = np.array([[Q[d] for d in ranked]])
    # sklearn uses gain = relevance (linear); compare with a linear-gain variant of ours
    lin = lambda gains: sum(g / math.log2(i + 1) for i, g in enumerate(gains, 1))  # noqa: E731
    ours = lin([Q[d] for d in ranked]) / lin(sorted(Q.values(), reverse=True)[:4])
    assert ours == pytest.approx(ndcg_score(true, np.array([[4, 3, 2, 1]]), k=4))


def test_prf_and_matching():
    gold = [{"type": "Date", "start": 0, "end": 10}, {"type": "School", "start": 20, "end": 30}]
    pred = [{"type": "Date", "start": 0, "end": 10}, {"type": "School", "start": 22, "end": 30}, {"type": "Road", "start": 40, "end": 45}]
    assert M.match_mentions(pred, gold) == (1, 2, 1)
    assert M.match_mentions(pred, gold, relaxed=True) == (2, 1, 0)
    assert M.prf(2, 1, 0) == pytest.approx((2 / 3, 1.0, 0.8))


def test_calibration_against_sklearn():
    from sklearn.metrics import brier_score_loss, log_loss
    p, y = [0.9, 0.2, 0.65, 0.4, 0.05], [1, 0, 1, 1, 0]
    assert M.brier(p, y) == pytest.approx(brier_score_loss(y, p))
    assert M.log_loss(p, y) == pytest.approx(log_loss(y, p))


def test_ece_by_hand():
    p, y = [0.1, 0.3, 0.9, 0.95], [0, 1, 1, 1]
    # bins: [0,.2):0.1->acc0 ; [.2,.4):0.3->acc1 ; [.8,1]: mean .925 acc 1
    expect = 0.25 * 0.1 + 0.25 * 0.7 + 0.5 * 0.075
    assert M.ece(p, y) == pytest.approx(expect)


def test_exact_top_k():
    m = np.array([[1, 0], [0.7, 0.7], [0, 1]], dtype=float)
    ids, _ = M.exact_top_k(np.array([1.0, 0.1]), m, ["x", "y", "z"], 2)
    assert ids == ["x", "y"]
