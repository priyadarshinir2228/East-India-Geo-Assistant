"""Task 2.3, 2.5, 2.6: score both extractors on gold_entities.jsonl (exact and relaxed P/R/F1 per type),
check LLM determinism at temperature 0 (twice) and 0.7, and time both methods."""
import argparse
import time
from collections import defaultdict

from common import config
from common.io import read_jsonl, write_md_table
from evalsuite.metrics import match_mentions, prf
from ingest import extract_rules
from ingest.chunking import chunk_document
from ingest.loaders import load_documents
from ingest.schema import ENTITY_TYPES


def run_doc(doc, method, gaz=None, temperature=0.0, seed=42):
    """Extract per chunk (as ingestion does) and return document-level mentions and stats."""
    from ingest import extract_llm
    found, secs, toks = {}, 0.0, 0
    for c in chunk_document(doc):
        t = time.perf_counter()
        if method == "rules":
            ms = extract_rules.extract(c["text"], gaz)
        else:
            ms, st = extract_llm.extract(c["text"], temperature=temperature, seed=seed)
            toks += st["completion_tokens"] or 0
        secs += time.perf_counter() - t
        for m in ms:
            key = (m["type"], m["start"] + c["start"], m["end"] + c["start"])
            found[key] = {"type": key[0], "start": key[1], "end": key[2], "text": m["text"]}
    return list(found.values()), secs, toks


def score(results, gold):
    rows = []
    for t in ENTITY_TYPES + ["ALL"]:
        ex, rx = [0, 0, 0], [0, 0, 0]
        for d, pred in results.items():
            p = [m for m in pred if t == "ALL" or m["type"] == t]
            g = [m for m in gold[d] if t == "ALL" or m["type"] == t]
            for i, v in enumerate(match_mentions(p, g)):
                ex[i] += v
            for i, v in enumerate(match_mentions(p, g, relaxed=True)):
                rx[i] += v
        rows.append([t, sum(1 for d in gold for m in gold[d] if t == "ALL" or m["type"] == t)] +
                    [f"{x:.2f}" for x in prf(*ex)] + [f"{x:.2f}" for x in prf(*rx)])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-llm", action="store_true")
    a = ap.parse_args()
    gold_rows = read_jsonl(config.EVAL_DIR / "gold_entities.jsonl")
    docs = {d["doc_id"]: d for d in load_documents()}
    gold = {g["doc_id"]: g["entities"] for g in gold_rows}
    gaz = extract_rules.Gazetteer()
    hdr = ["Type", "Gold", "P exact", "R exact", "F1 exact", "P relaxed", "R relaxed", "F1 relaxed"]
    timing = []
    res, secs = {}, 0.0
    for d in gold:
        res[d], s, _ = run_doc(docs[d], "rules", gaz)
        secs += s
    write_md_table(config.RESULTS / "task2_extraction_rules.md", "Task 2: rules + gazetteer extractor", hdr, score(res, gold))
    timing.append(["rules + gazetteer", f"{secs / len(gold) * 1000:.1f} ms", "-"])
    if a.skip_llm:
        return
    runs = {}
    for name, temp, seed in [("t0_a", 0.0, 42), ("t0_b", 0.0, 7), ("t07", 0.7, 7)]:
        r, secs, toks = {}, 0.0, 0
        for d in gold:
            r[d], s, k = run_doc(docs[d], "llm", temperature=temp, seed=seed)
            secs, toks = secs + s, toks + k
        runs[name] = r
        if name == "t0_a":
            write_md_table(config.RESULTS / "task2_extraction_llm.md", "Task 2: LLM extractor (temperature 0)", hdr, score(r, gold))
            timing.append(["LLM (temperature 0)", f"{secs / len(gold):.2f} s", f"{toks / secs:.1f}" if secs else "-"])
    diff = lambda x, y: sum(len({(m["type"], m["start"], m["end"]) for m in x[d]} ^  # noqa: E731
                                {(m["type"], m["start"], m["end"]) for m in y[d]}) for d in gold)
    total = sum(len(runs["t0_a"][d]) for d in gold)
    write_md_table(config.RESULTS / "task2_determinism.md", "Task 2: LLM determinism",
                   ["Comparison", "Mentions differing (symmetric difference)", "Mentions in run A"],
                   [["temp 0 run A vs temp 0 run B (different seed)", diff(runs["t0_a"], runs["t0_b"]), total],
                    ["temp 0 run A vs temp 0.7", diff(runs["t0_a"], runs["t07"]), total]],
                   notes="F1 at temperature 0.7 (exact, ALL): " + score(runs["t07"], gold)[-1][4])
    write_md_table(config.RESULTS / "task2_timing.md", "Task 2: time per document", ["Method", "Time per document", "Tokens/s"], timing)


if __name__ == "__main__":
    main()
