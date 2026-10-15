"""Task 7.1-7.5: confidence signals, combination, calibration, temperature scaling, abstention threshold.

Success label for each question: the top reranked passage has grade 1 or 2.
Fit everything (temperature T, logistic regression, threshold) on the 25 "fit" questions only;
report on the 15 "test" questions.
"""
import json
import math
from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression

from app import pipeline
from common import config
from common.io import write_md_table
from evalsuite import qrels as Q
from evalsuite.metrics import brier, ece, log_loss, mean, reliability_table
from retrieve import confidence as C


def answer_agreement(question, top, facts, n=5):
    """Fallback when the server returns no log-probabilities: share of 5 sampled answers that agree
    with the majority answer (normalised text)."""
    outs = [pipeline.generate(question, top, facts, temperature=0.7, top_p=0.95, seed=s)[0]["answer"] for s in range(n)]
    norm = [" ".join(o.lower().split())[:80] for o in outs]
    return Counter(norm).most_common(1)[0][1] / n


def collect():
    rows = []
    for q in Q.load("calibration_questions.jsonl"):
        rr = pipeline.retrieve_and_rank(q["question"])
        top = rr["ranked"][:5]
        facts = pipeline.graph_facts(rr["entities"])
        obj, res = pipeline.generate(q["question"], top, facts)
        lp = res.get("token_logprobs") or []
        rows.append({"id": q["id"], "split": q["split"], "scores": [d["rerank_score"] for d in rr["ranked"][:2]],
                     "label": int(bool(rr["ranked"]) and q["qrels"].get(rr["ranked"][0]["chunk_id"], 0) >= 1),
                     "agree": float(rr["ranked"][0]["chunk_id"] in rr["kw_ids"][:5] and rr["ranked"][0]["chunk_id"] in rr["vec_ids"][:5]),
                     "lp_mean": math.exp(sum(lp) / len(lp)) if lp else answer_agreement(q["question"], top, facts),
                     "has_logprobs": bool(lp)})
    return rows


def features(r, T):
    s1, s2 = (r["scores"] + [-10, -10])[:2]
    p1, p2 = C.sigmoid(s1 / T), C.sigmoid(s2 / T)
    return [p1, p1 - p2, r["agree"], r["lp_mean"]]


def main():
    rows = collect()
    (config.RESULTS / "task7_calibration_rows.json").write_text(json.dumps(rows, indent=1))
    fit, test = [r for r in rows if r["split"] == "fit"], [r for r in rows if r["split"] == "test"]
    yf, yt = [r["label"] for r in fit], [r["label"] for r in test]

    # temperature scaling of the reranker score alone (7.4)
    grid = [0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0]
    tl = [(T, log_loss([C.sigmoid(r["scores"][0] / T) for r in fit], yf)) for T in grid]
    T_best = min(tl, key=lambda x: x[1])[0]
    p_t1 = [C.sigmoid(r["scores"][0]) for r in test]
    p_tb = [C.sigmoid(r["scores"][0] / T_best) for r in test]

    # combined confidence (7.2): logistic regression on fit only
    Xf, Xt = np.array([features(r, T_best) for r in fit]), np.array([features(r, T_best) for r in test])
    lr = LogisticRegression(C=1.0).fit(Xf, yf) if len(set(yf)) > 1 else None
    coef = lr.coef_[0].tolist() if lr else [4.0, 1.0, 0.5, 1.0]
    intercept = float(lr.intercept_[0]) if lr else -3.0
    comb = lambda X: [C.sigmoid(intercept + float(np.dot(coef, x))) for x in X]  # noqa: E731
    pf, pt = comb(Xf), comb(Xt)

    # reliability table + ECE + Brier (7.3)
    rel = reliability_table(pt, yt, 5)
    over = mean(pt) > mean(yt)
    # abstention (7.5): choose on fit the lowest threshold with >= 90% accuracy on answered questions
    def cov_acc(p, y, th):
        ans = [yy for pp, yy in zip(p, y) if pp >= th]
        return len(ans) / len(y), (mean(ans) if ans else float("nan"))
    ths = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    meets = [th for th in ths if cov_acc(pf, yf, th)[0] > 0 and cov_acc(pf, yf, th)[1] >= 0.9]
    # if no threshold reaches 90% on fit, fall back to the one with the best accuracy (and say so)
    chosen = meets[0] if meets else max((th for th in ths if cov_acc(pf, yf, th)[0] > 0),
                                        key=lambda th: cov_acc(pf, yf, th)[1], default=0.5)
    trows = []
    for th in ths:
        cf, af = cov_acc(pf, yf, th)
        ct, at = cov_acc(pt, yt, th)
        trows.append([th, f"{cf:.2f}", f"{af:.2f}", f"{ct:.2f}", f"{at:.2f}", "chosen" if th == chosen else ""])

    model = {"T": T_best, "coef": coef, "intercept": intercept, "threshold": chosen, "features": C.FEATURES,
             "uses_logprobs": all(r["has_logprobs"] for r in rows)}
    C.MODEL_FILE.write_text(json.dumps(model, indent=1))

    sig_rows = [[r["id"], r["split"], f"{features(r, T_best)[0]:.2f}", f"{features(r, T_best)[1]:.2f}", int(r["agree"]),
                 f"{r['lp_mean']:.2f}", f"{p:.2f}", r["label"]] for r, p in zip(fit + test, pf + pt)]
    write_md_table(config.RESULTS / "task7_signals.md", "Task 7: signals per question",
                   ["Question", "Split", "p_top", "margin", "agree", "lp_mean" if model["uses_logprobs"] else "agreement@5",
                    "Combined", "Label"], sig_rows,
                   notes=("Answer signal = exp(mean token log-probability) under greedy decoding." if model["uses_logprobs"] else
                          "The model server returned no log-probabilities, so the answer signal is agreement across five sampled answers (temperature 0.7)."))
    write_md_table(config.RESULTS / "task7_calibration.md", "Task 7: reliability on test (15 questions, 5 bins)",
                   ["Bin", "Count", "Mean confidence", "Success rate"],
                   [[f"{lo:.1f}-{hi:.1f}", c, "-" if conf is None else f"{conf:.2f}", "-" if acc is None else f"{acc:.2f}"]
                    for lo, hi, c, conf, acc in rel],
                   notes=f"ECE = {ece(pt, yt):.3f}, Brier = {brier(pt, yt):.3f} (combined, test). "
                         f"Mean confidence {mean(pt):.2f} vs success rate {mean(yt):.2f}: the system is "
                         f"{'over' if over else 'under'}-confident on average.\n\n"
                         f"Logistic regression weights {dict(zip(C.FEATURES, [round(c, 3) for c in coef]))}, intercept {intercept:.3f}.\n\n"
                         "**Temperature scaling of the reranker probability (p_top alone)**\n\n"
                         "| T | log loss on fit |\n|---|---|\n" + "\n".join(f"| {T} | {l:.3f} |" for T, l in tl) +
                         f"\n\nChosen T = {T_best}. Test ECE of sigmoid(s): T=1 -> {ece(p_t1, yt):.3f}; T={T_best} -> {ece(p_tb, yt):.3f}.")
    write_md_table(config.RESULTS / "task7_abstention.md", "Task 7: coverage and accuracy by threshold",
                   ["Threshold", "Coverage (fit)", "Accuracy (fit)", "Coverage (test)", "Accuracy (test)", ""], trows,
                   notes=(f"Threshold {chosen} is the lowest with >= 90% accuracy on the fit questions" if meets else
                          f"No threshold reached 90% accuracy on the fit questions; {chosen} gave the best accuracy") +
                         f". It is saved to {C.MODEL_FILE.name} and used by the assistant.")


if __name__ == "__main__":
    main()
