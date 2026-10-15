"""Four retrieval modes (Task 5), all returning ranked chunks with scores.

keyword: BM25 via a match query      vector: approximate kNN on the dense_vector field
hybrid:  reciprocal rank fusion (RRF) of keyword + vector, or a weighted score combination
graph:   hybrid + chunks from graph expansion, fused as a third RRF list
Optional filters: metadata (doc_kind, boards, issued date range) and geo_distance on school locations.
"""
from common import config
from common.es import app_client
from common.models import get_embedder

RRF_K = 60            # rank constant: larger -> flatter weights across ranks (tuned in eval_retrieval)
CANDIDATES = 50       # how deep each list is read before fusing
NUM_CANDIDATES = 100  # HNSW candidates per shard for kNN
GRAPH_WEIGHT = 0.5    # weight of the graph list inside RRF
SRC = ["chunk_id", "doc_id", "title", "text", "page", "start", "end", "doc_kind", "issued_date", "school_ids", "boards"]

_es = {}


def es():
    if "c" not in _es:
        _es["c"] = app_client()
    return _es["c"]


def build_filters(meta=None, geo=None):
    f = []
    meta = meta or {}
    if meta.get("doc_kind"):
        f.append({"terms": {"doc_kind": meta["doc_kind"]}})
    if meta.get("boards"):
        f.append({"terms": {"boards": meta["boards"]}})
    if meta.get("issued_after") or meta.get("issued_before"):
        f.append({"range": {"issued_date": {k: v for k, v in [("gte", meta.get("issued_after")),
                                                               ("lte", meta.get("issued_before"))] if v}}})
    if geo:  # {"lat":..., "lon":..., "distance": "2km"}
        f.append({"geo_distance": {"distance": geo["distance"], "location": {"lat": geo["lat"], "lon": geo["lon"]}}})
    return f


def _hits(resp):
    return [{**h["_source"], "score": h["_score"]} for h in resp["hits"]["hits"]]


def keyword(query, k=10, meta=None, geo=None):
    body = {"bool": {"must": [{"match": {"text": query}}], "filter": build_filters(meta, geo)}}
    return _hits(es().search(index=config.CHUNKS_INDEX, query=body, size=k, source=SRC))


def vector(query, k=10, meta=None, geo=None, num_candidates=NUM_CANDIDATES, field="embedding", qvec=None):
    qv = qvec if qvec is not None else get_embedder().query(query)
    knn = {"field": field, "query_vector": [float(x) for x in qv], "k": k, "num_candidates": max(num_candidates, k)}
    flt = build_filters(meta, geo)
    if flt:
        knn["filter"] = flt  # filtering happens inside the HNSW search, so k results still come back
    return _hits(es().search(index=config.CHUNKS_INDEX, knn=knn, size=k, source=SRC))


def rrf(lists, k_const=RRF_K, weights=None):
    """Reciprocal rank fusion: score(d) = sum_i w_i / (k + rank_i(d)). Ties broken by chunk_id."""
    weights = weights or [1.0] * len(lists)
    scores, docs = {}, {}
    for w, lst in zip(weights, lists):
        for rank, d in enumerate(lst, start=1):
            scores[d["chunk_id"]] = scores.get(d["chunk_id"], 0.0) + w / (k_const + rank)
            docs.setdefault(d["chunk_id"], d)
    order = sorted(scores, key=lambda c: (-scores[c], c))
    return [{**docs[c], "score": scores[c]} for c in order]


def weighted(lists, alphas):
    """Min-max normalise each list's scores to [0, 1], then add them with weights alphas."""
    scores, docs = {}, {}
    for a, lst in zip(alphas, lists):
        if not lst:
            continue
        hi, lo = max(d["score"] for d in lst), min(d["score"] for d in lst)
        for d in lst:
            s = (d["score"] - lo) / (hi - lo) if hi > lo else 1.0
            scores[d["chunk_id"]] = scores.get(d["chunk_id"], 0.0) + a * s
            docs.setdefault(d["chunk_id"], d)
    order = sorted(scores, key=lambda c: (-scores[c], c))
    return [{**docs[c], "score": scores[c]} for c in order]


def hybrid(query, k=10, meta=None, geo=None, method="rrf", k_const=RRF_K, alpha=0.5, depth=CANDIDATES):
    kw, vec = keyword(query, depth, meta, geo), vector(query, depth, meta, geo)
    fused = rrf([kw, vec], k_const) if method == "rrf" else weighted([kw, vec], [alpha, 1 - alpha])
    return fused[:k]


def fetch_chunks(chunk_ids, meta=None, geo=None):
    if not chunk_ids:
        return {}
    q = {"bool": {"filter": [{"ids": {"values": list(chunk_ids)}}] + build_filters(meta, geo)}}
    r = es().search(index=config.CHUNKS_INDEX, query=q, size=len(chunk_ids), source=SRC)
    return {h["_source"]["chunk_id"]: h["_source"] for h in r["hits"]["hits"]}


def graph_hybrid(query, k=10, meta=None, geo=None, query_entities=None, k_const=RRF_K,
                 graph_weight=GRAPH_WEIGHT, depth=CANDIDATES, hops=2):
    from retrieve.entities import detect
    from retrieve.graph import expand
    kw, vec = keyword(query, depth, meta, geo), vector(query, depth, meta, geo)
    ents = query_entities if query_entities is not None else [e["entity_id"] for e in detect(query)]
    exp = expand(ents, hops=hops)[:depth]
    got = fetch_chunks([x["chunk_id"] for x in exp], meta, geo)
    glist = [{**got[x["chunk_id"]], "score": x["score"], "graph_path": x["path"]} for x in exp if x["chunk_id"] in got]
    fused = rrf([kw, vec, glist], k_const, weights=[1.0, 1.0, graph_weight])
    paths = {g["chunk_id"]: g["graph_path"] for g in glist}
    return [{**d, "graph_path": paths.get(d["chunk_id"], [])} for d in fused[:k]]


MODES = {"keyword": keyword, "vector": vector, "hybrid": hybrid, "graph": graph_hybrid}
