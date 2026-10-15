"""In-memory graph over the relations index (Task 4): traversal, measures and expansion."""
from collections import Counter, defaultdict

import networkx as nx
from elasticsearch import helpers

from common import config
from common.es import app_client

HUB_DEGREE = 20      # nodes with more links than this are hubs (boards, big localities)
HUB_PENALTY = 0.5    # a path that passes *through* a hub keeps half its weight
_G = {}


def load_graph(es=None):
    """Build a MultiDiGraph from east_india_relations and remember entity -> chunk links."""
    if "g" in _G:
        return _G["g"]
    es = es or app_client()
    G = nx.MultiDiGraph()
    for hit in helpers.scan(es, index=config.RELATIONS_INDEX, query={"query": {"match_all": {}}}):
        r = hit["_source"]
        G.add_edge(r["source_id"], r["target_id"], key=r["type"], type=r["type"], weight=r["weight"],
                   evidence=r["evidence"])
    chunks_of, names = defaultdict(set), {}
    for hit in helpers.scan(es, index=config.ENTITIES_INDEX, query={"query": {"match_all": {}}},
                            _source=["entity_id", "type", "canonical_name", "mentions.chunk_id"]):
        e = hit["_source"]
        names[e["entity_id"]] = (e["type"], e["canonical_name"])
        for m in e.get("mentions", []):
            chunks_of[e["entity_id"]].add(m["chunk_id"])
        if e["entity_id"] in G:
            G.nodes[e["entity_id"]].update(type=e["type"], name=e["canonical_name"])
    _G.update(g=G, chunks_of=chunks_of, names=names)
    return G


def neighbours(entity_id, hops=2, types=None, max_expand=25, G=None):
    """Breadth-first search up to `hops` steps, following edges in both directions.

    - cycles: a node is never visited twice (visited set), so A->B->A loops stop at once
    - fan-out: at each step only the `max_expand` best frontier nodes (by path weight) are expanded
    - returns {node: {"hops", "weight", "path": [(src, type, dst), ...]}} for every reached node
    """
    G = G or load_graph()
    if entity_id not in G:
        return {}
    reached = {entity_id: {"hops": 0, "weight": 1.0, "path": []}}
    frontier = [entity_id]
    for step in range(1, hops + 1):
        frontier.sort(key=lambda n: -reached[n]["weight"])
        nxt = []
        for node in frontier[:max_expand]:
            through_hub = node != entity_id and G.degree(node) > HUB_DEGREE
            edges = [(node, v, d, (node, d["type"], v)) for _, v, d in G.out_edges(node, data=True)] + \
                    [(node, u, d, (u, d["type"], node)) for u, _, d in G.in_edges(node, data=True)]
            for _, other, d, triple in edges:
                if types and d["type"] not in types:
                    continue
                if other in reached:  # already visited: cycle or a second, longer route
                    continue
                w = reached[node]["weight"] * d["weight"] * (HUB_PENALTY if through_hub else 1.0)
                reached[other] = {"hops": step, "weight": w, "path": reached[node]["path"] + [triple]}
                nxt.append(other)
        frontier = nxt
    return reached


def expand(query_entities, hops=2, types=None, min_weight=0.3, max_expand=25):
    """Chunk IDs linked to entities within `hops` of the query entities, with a score and the path.

    A chunk is linked when it mentions a reached entity or is the evidence for an edge on the path.
    Score = the best path weight that reaches it. Paths weaker than min_weight are dropped (noise control).
    """
    G = load_graph()
    chunks_of = _G["chunks_of"]
    best = {}
    for q in query_entities:
        for node, info in neighbours(q, hops, types, max_expand, G).items():
            if info["weight"] < min_weight:
                continue
            cands = set(chunks_of.get(node, ()))
            for s, t, dst in info["path"]:
                ev = G.edges[s, dst, t]["evidence"] if G.has_edge(s, dst, t) else None
                if ev and ev not in ("geoserver", "dates_and_subject"):
                    cands.add(ev)
            for c in cands:
                if c not in best or info["weight"] > best[c]["score"]:
                    best[c] = {"chunk_id": c, "score": info["weight"], "entity": node, "path": info["path"]}
    return sorted(best.values(), key=lambda x: (-x["score"], x["chunk_id"]))


def graph_measures(G=None):
    G = G or load_graph()
    U = G.to_undirected()
    deg = sorted(G.degree(), key=lambda kv: (-kv[1], kv[0]))[:5]
    simple = nx.DiGraph()
    for u, v, d in G.edges(data=True):  # PageRank on the weighted simple graph
        w = simple[u][v]["weight"] + d["weight"] if simple.has_edge(u, v) else d["weight"]
        simple.add_edge(u, v, weight=w)
    pr = nx.pagerank(simple.to_undirected(), weight="weight")
    top_pr = sorted(pr.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
            "components": nx.number_connected_components(U), "top_degree": deg, "top_pagerank": top_pr,
            "edge_types": dict(sorted(Counter(d["type"] for *_, d in G.edges(data=True)).items()))}


def name_of(eid):
    load_graph()
    return _G["names"].get(eid, (None, eid))[1]


def path_str(path):
    return " -> ".join(f"{name_of(s)} [{t}] {name_of(d)}" for s, t, d in path) if path else ""

