"""Turn evidence-based judgments into chunk-level relevance grades.

A chunk gets a judgment's grade when it contains the whole evidence string (chunks overlap,
so a fact on a boundary is still whole in one of them). A chunk takes the highest grade it earns.
"""
from common import config
from common.io import read_jsonl

_chunks = {}


def chunks():
    if not _chunks:
        for c in read_jsonl(config.WORK / "chunks.jsonl"):
            _chunks[c["chunk_id"]] = c
    return _chunks


def qrels_for(judgments):
    out = {}
    for j in judgments:
        for cid, c in chunks().items():
            if c["doc_id"] == j["doc_id"] and j["evidence"] in c["text"]:
                out[cid] = max(out.get(cid, 0), j["grade"])
    return out


def load(name):
    rows = read_jsonl(config.EVAL_DIR / name)
    for r in rows:
        r["qrels"] = qrels_for(r.get("judgments", []))
    return rows
