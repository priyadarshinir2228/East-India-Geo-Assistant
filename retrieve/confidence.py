"""Confidence for an answer (Task 7): signals -> one calibrated probability -> answer or abstain.

Signals per question:
  p_top     sigmoid(top reranker score / T)        how sure the cross-encoder is about passage 1
  margin    sigmoid(s1 / T) - sigmoid(s2 / T)      how clearly passage 1 beats passage 2
  agree     1 if the top passage is in both the keyword top-5 and the vector top-5
  lp_mean   exp(mean token log-probability) of the greedy answer (geometric-mean token probability)
The combiner is a logistic regression fitted on the "fit" questions only; the fitted weights,
temperature T and abstention threshold are stored in evalsuite/results/confidence_model.json.
"""
import json
import math

from common import config

MODEL_FILE = config.RESULTS / "confidence_model.json"
FEATURES = ["p_top", "margin", "agree", "lp_mean"]


def sigmoid(x):
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def signals(reranked, kw_ids, vec_ids, answer_logprobs=None, T=1.0):
    s = [d["rerank_score"] for d in reranked] + [-10.0, -10.0]
    p1, p2 = sigmoid(s[0] / T), sigmoid(s[1] / T)
    top = reranked[0]["chunk_id"] if reranked else None
    lp = answer_logprobs or []
    return {"p_top": p1, "margin": p1 - p2, "agree": float(top in kw_ids[:5] and top in vec_ids[:5]),
            "lp_mean": math.exp(sum(lp) / len(lp)) if lp else 0.5}


def load_model():
    if MODEL_FILE.exists():
        return json.loads(MODEL_FILE.read_text())
    # defaults until evalsuite/eval_confidence.py has been run
    return {"T": 1.0, "coef": [4.0, 1.0, 0.5, 1.0], "intercept": -3.0, "threshold": 0.5, "uses_logprobs": True}


def combine(sig, model=None):
    model = model or load_model()
    z = model["intercept"] + sum(c * sig[f] for c, f in zip(model["coef"], FEATURES))
    return sigmoid(z)
